import Foundation

enum LTXError: LocalizedError, Equatable {
    case pythonNotConfigured
    case modelLoadFailed(String)
    case generationFailed(String)
    case exportFailed(String)
    case cancelled
    
    var errorDescription: String? {
        switch self {
        case .pythonNotConfigured:
            return "Python environment not configured. Please check Preferences."
        case .modelLoadFailed(let msg):
            return "Failed to load LTX model: \(msg)"
        case .generationFailed(let msg):
            return "Generation failed: \(msg)"
        case .exportFailed(let msg):
            return "Failed to export video: \(msg)"
        case .cancelled:
            return "Generation was cancelled"
        }
    }
}

// Use subprocess to run MLX-based generation
class LTXBridge {
    static let shared = LTXBridge()
    
    private(set) var isModelLoaded = false
    private var pythonHome: String?
    private var pythonExecutable: String?
    
    // Server process management
    private var serverProcess: Process?
    private var serverInputPipe: Pipe?
    private var serverOutputPipe: Pipe?
    private var serverErrorPipe: Pipe?

    // Server communication state
    private let serverLock = NSLock()
    private var currentProgressHandler: ((Double, String) -> Void)?
    private var currentResponseContinuation: CheckedContinuation<[String: Any], Error>?
    private var stderrAccumulator = ""
    private var stdoutAccumulator = ""
    private var capturedEnhancedPrompt: String?
    private var serverInitContinuation: CheckedContinuation<Void, Error>?

    private init() {
        setupPythonPaths()
    }
    
    private func setupPythonPaths() {
        // Get Python path from user defaults
        guard let savedPath = UserDefaults.standard.string(forKey: "pythonPath"),
              !savedPath.isEmpty else {
            pythonExecutable = nil
            pythonHome = nil
            return
        }
        
        // Use PythonEnvironment's path detection to handle both executable and dylib paths
        let pathType = PythonEnvironment.shared.detectPathType(savedPath)
        
        switch pathType {
        case .executable:
            pythonExecutable = savedPath
            if let dylib = PythonEnvironment.shared.executableToDylib(savedPath),
               let home = PythonEnvironment.shared.extractPythonHome(from: dylib) {
                pythonHome = home
            } else {
                let execURL = URL(fileURLWithPath: savedPath)
                pythonHome = execURL.deletingLastPathComponent().deletingLastPathComponent().path
            }
            
        case .dylib:
            if let exec = PythonEnvironment.shared.dylibToExecutable(savedPath) {
                pythonExecutable = exec
            }
            if let home = PythonEnvironment.shared.extractPythonHome(from: savedPath) {
                pythonHome = home
                if pythonExecutable == nil {
                    let standardExec = "\(home)/bin/python3"
                    if FileManager.default.isExecutableFile(atPath: standardExec) {
                        pythonExecutable = standardExec
                    }
                }
            }
            
        case .unknown:
            if FileManager.default.isExecutableFile(atPath: savedPath) {
                pythonExecutable = savedPath
                let execURL = URL(fileURLWithPath: savedPath)
                pythonHome = execURL.deletingLastPathComponent().deletingLastPathComponent().path
            } else {
                pythonExecutable = nil
                pythonHome = nil
            }
        }
    }
    
    func loadModel(progressHandler: @escaping (String) -> Void) async throws {
        setupPythonPaths()
        
        guard let _ = pythonExecutable else {
            throw LTXError.pythonNotConfigured
        }
        
        try await startServerIfNeeded(progressHandler: progressHandler)
        isModelLoaded = true
    }

    func unloadModel() async {
        stopServer()
        isModelLoaded = false
    }

    private func stopServer() {
        serverLock.lock()
        defer { serverLock.unlock() }

        if let process = serverProcess {
            process.terminate()
            serverProcess = nil
        }
        serverInputPipe = nil
        serverOutputPipe = nil
        serverErrorPipe = nil
        currentResponseContinuation?.resume(throwing: LTXError.cancelled)
        currentResponseContinuation = nil
        serverInitContinuation?.resume(throwing: LTXError.cancelled)
        serverInitContinuation = nil
    }

    private func startServerIfNeeded(progressHandler: ((String) -> Void)? = nil) async throws {
        serverLock.lock()
        if serverProcess != nil && serverProcess!.isRunning {
            serverLock.unlock()
            return
        }
        
        // Cleanup if dead process exists
        if serverProcess != nil {
            serverProcess = nil
            serverInputPipe = nil
            serverOutputPipe = nil
            serverErrorPipe = nil
        }
        serverLock.unlock()
        
        guard let python = pythonExecutable else {
            throw LTXError.pythonNotConfigured
        }
        
        let resourcesPath = Bundle.main.bundlePath + "/Contents/Resources"
        let scriptPath = resourcesPath + "/ltx_server.py"

        progressHandler?("Starting LTX Server...")

        try await withCheckedThrowingContinuation { continuation in
            serverLock.lock()
            self.serverInitContinuation = continuation
            serverLock.unlock()

            DispatchQueue.global(qos: .userInitiated).async {
                let process = Process()
                process.executableURL = URL(fileURLWithPath: python)
                process.arguments = ["-u", scriptPath]

                var env: [String: String] = [:]
                let pythonBin = URL(fileURLWithPath: python).deletingLastPathComponent().path
                env["PATH"] = "\(pythonBin):/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
                env["HOME"] = ProcessInfo.processInfo.environment["HOME"] ?? ""
                env["USER"] = ProcessInfo.processInfo.environment["USER"] ?? ""
                env["TMPDIR"] = ProcessInfo.processInfo.environment["TMPDIR"] ?? "/tmp"
                if let metalDevice = ProcessInfo.processInfo.environment["MTL_DEVICE_WRAPPER_TYPE"] {
                    env["MTL_DEVICE_WRAPPER_TYPE"] = metalDevice
                }
                process.environment = env

                let stdin = Pipe()
                let stdout = Pipe()
                let stderr = Pipe()

                process.standardInput = stdin
                process.standardOutput = stdout
                process.standardError = stderr

                // Read stdout (JSON responses)
                stdout.fileHandleForReading.readabilityHandler = { [weak self] handle in
                    let data = handle.availableData
                    if !data.isEmpty, let str = String(data: data, encoding: .utf8) {
                        self?.handleServerOutput(str)
                    }
                }

                // Read stderr (Logs, Progress, Init status)
                stderr.fileHandleForReading.readabilityHandler = { [weak self] handle in
                    let data = handle.availableData
                    if !data.isEmpty, let str = String(data: data, encoding: .utf8) {
                        self?.handleServerError(str)
                    }
                }

                do {
                    try process.run()
                    self.serverLock.lock()
                    self.serverProcess = process
                    self.serverInputPipe = stdin
                    self.serverOutputPipe = stdout
                    self.serverErrorPipe = stderr
                    self.serverLock.unlock()

                    process.terminationHandler = { [weak self] _ in
                        self?.handleServerTermination()
                    }
                } catch {
                    self.serverLock.lock()
                    self.serverInitContinuation?.resume(throwing: error)
                    self.serverInitContinuation = nil
                    self.serverLock.unlock()
                }
            }
        }
    }

    private func handleServerOutput(_ text: String) {
        serverLock.lock()
        defer { serverLock.unlock() }

        stdoutAccumulator += text
        if let range = stdoutAccumulator.range(of: "\n") {
            let line = String(stdoutAccumulator[..<range.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
            stdoutAccumulator.removeSubrange(..<range.upperBound)

            if !line.isEmpty {
                if let data = line.data(using: .utf8),
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    currentResponseContinuation?.resume(returning: json)
                    currentResponseContinuation = nil
                }
            }
        }
    }

    private func handleServerError(_ text: String) {
        // Log to file for debugging
        let logFile = "/tmp/ltx_generation.log"
        if let logData = ("[STDERR] " + text).data(using: .utf8) {
            if FileManager.default.fileExists(atPath: logFile) {
                if let handle = FileHandle(forWritingAtPath: logFile) {
                    handle.seekToEndOfFile()
                    handle.write(logData)
                    handle.closeFile()
                }
            } else {
                try? logData.write(to: URL(fileURLWithPath: logFile))
            }
        }

        // Accumulate and split by line
        // Assuming line buffering is working reasonably well, but we should be robust
        // Simple print for debug
        print("[LTX-SERVER] \(text)", terminator: "")

        let lines = text.components(separatedBy: "\n")
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty { continue }

            if trimmed == "SERVER_READY" {
                serverLock.lock()
                serverInitContinuation?.resume()
                serverInitContinuation = nil
                serverLock.unlock()
                continue
            }

            if trimmed.hasPrefix("STATUS:") {
                let msg = String(trimmed.dropFirst(7))
                currentProgressHandler?(0, msg) // 0 means indeterminate/keep previous
            } else if trimmed.lowercased().hasPrefix("enhanced prompt:") {
                serverLock.lock()
                capturedEnhancedPrompt = String(trimmed.dropFirst("enhanced prompt:".count)).trimmingCharacters(in: .whitespacesAndNewlines)
                serverLock.unlock()
            } else if trimmed.hasPrefix("ENHANCED_PROMPT:") {
                serverLock.lock()
                capturedEnhancedPrompt = String(trimmed.dropFirst("ENHANCED_PROMPT:".count)).trimmingCharacters(in: .whitespacesAndNewlines)
                serverLock.unlock()
            } else if trimmed.hasPrefix("PROGRESS:") {
                let parts = trimmed.split(separator: ":")
                if parts.count >= 3 {
                    let val = Double(parts[1]) ?? 0
                    let msg = String(parts[2])
                    currentProgressHandler?(val, msg)
                }
            } else if trimmed.hasPrefix("STAGE:") {
                // Parse stage-aware progress: STAGE:1:STEP:3:8:Denoising
                let parts = trimmed.components(separatedBy: ":")
                if parts.count >= 5,
                   let stage = Int(parts[1]),
                   let step = Int(parts[3]),
                   let total = Int(parts[4]) {
                    let stageProgress = Double(step) / Double(total)
                    let mappedProgress: Double
                    let message: String

                    if stage == 1 {
                        mappedProgress = 0.1 + (stageProgress * 0.4)
                        message = "Stage 1 (\(step)/\(total)): Generating at half resolution"
                    } else {
                        mappedProgress = 0.5 + (stageProgress * 0.4)
                        message = "Stage 2 (\(step)/\(total)): Refining at full resolution"
                    }
                    currentProgressHandler?(mappedProgress, message)
                }
            }
            // Capture library logs if needed, but we rely on STAGE output mainly.
            // Also handle DOWNLOAD progress if server forwards it (it should if stderr is redirected)
            else if trimmed.hasPrefix("DOWNLOAD:PROGRESS:") {
                 // ... reuse parsing logic if needed, but server might not emit this exact format unless mlx_video does
                 // mlx_video (tqdm) prints to stderr.
                 // We can implement tqdm parsing here too if we want.
            }
        }
    }

    private func handleServerTermination() {
        serverLock.lock()
        defer { serverLock.unlock() }

        isModelLoaded = false
        serverProcess = nil
        serverInputPipe = nil
        serverOutputPipe = nil
        serverErrorPipe = nil

        currentResponseContinuation?.resume(throwing: LTXError.generationFailed("Server process terminated unexpectedly"))
        currentResponseContinuation = nil
        serverInitContinuation?.resume(throwing: LTXError.generationFailed("Server process terminated during initialization"))
        serverInitContinuation = nil
    }
    
    func generate(
        request: GenerationRequest,
        outputPath: String,
        progressHandler: @escaping (Double, String) -> Void
    ) async throws -> (videoPath: String, seed: Int, enhancedPrompt: String?) {
        setupPythonPaths()
        
        try await startServerIfNeeded(progressHandler: { msg in
             progressHandler(0.05, msg)
        })
        
        let params = request.parameters
        let seed = params.seed ?? Int.random(in: 0..<Int(Int32.max))
        let modelRepo = LTXModelVariant.modelRepo
        
        // Prepare request parameters
        var genParams: [String: Any] = [
            "prompt": request.prompt,
            "height": (params.height / 64) * 64,
            "width": (params.width / 64) * 64,
            "num_frames": params.numFrames,
            "seed": seed,
            "fps": params.fps,
            "output_path": outputPath,
            "model_repo": modelRepo,
            "tiling": params.vaeTilingMode,
            "no_audio": request.disableAudio,
            "save_audio_separately": UserDefaults.standard.bool(forKey: "saveAudioTrackSeparately"),
            "enhance_prompt": UserDefaults.standard.bool(forKey: "enableGemmaPromptEnhancement"),
            "use_uncensored_enhancer": UserDefaults.standard.bool(forKey: "enableGemmaPromptEnhancement"),
            "top_p": request.gemmaTopP,
            "temperature": request.gemmaTopP, // Mapping top_p to temperature for enhancer per old code?
            // Old code: cmd.extend(["--temperature", str(\(request.gemmaTopP))])
            // Wait, old code used top_p from UI as temperature?
            // "help": "Temperature for prompt enhancement"
            // Yes, it seems so.
        ]
        
        if let imagePath = request.sourceImagePath {
            genParams["image"] = imagePath
            genParams["image_strength"] = params.imageStrength
        }
        
        let req: [String: Any] = [
            "command": "generate",
            "params": genParams
        ]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: req),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            throw LTXError.generationFailed("Failed to create request JSON")
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            serverLock.lock()
            if currentResponseContinuation != nil {
                serverLock.unlock()
                continuation.resume(throwing: LTXError.generationFailed("Another generation is in progress"))
                return
            }
            
            currentResponseContinuation = continuation
            currentProgressHandler = progressHandler
            stdoutAccumulator = "" // Clear accumulator
            capturedEnhancedPrompt = nil // Clear previous prompt

            guard let input = serverInputPipe else {
                serverLock.unlock()
                continuation.resume(throwing: LTXError.generationFailed("Server not connected"))
                return
            }

            // Send request
            let inputData = (jsonString + "\n").data(using: .utf8)!
            input.fileHandleForWriting.write(inputData)
            serverLock.unlock()
        }.map { response in
            // Check for success
            if let success = response["success"] as? Bool, !success {
                let errorMsg = response["error"] as? String ?? "Unknown server error"
                throw LTXError.generationFailed(errorMsg)
            }

            // Map response to tuple
            let videoPath = response["video_path"] as? String ?? outputPath
            let seed = response["seed"] as? Int ?? seed

            // Retrieve captured enhanced prompt with lock
            self.serverLock.lock()
            let prompt = self.capturedEnhancedPrompt
            self.serverLock.unlock()

            return (videoPath, seed, prompt)
        }
    }

    /// Preview enhanced prompt without running generation. Returns enhanced text or nil on error.
    func previewEnhancedPrompt(
        prompt: String,
        modelRepo: String,
        temperature: Double,
        sourceImagePath: String?,
        progressHandler: @escaping (String) -> Void
    ) async throws -> String? {
        setupPythonPaths()
        guard let python = pythonExecutable else {
            throw LTXError.pythonNotConfigured
        }
        let resourcesPath = Bundle.main.bundlePath + "/Contents/Resources"
        let scriptPath = resourcesPath + "/enhance_prompt_preview.py"
        guard FileManager.default.fileExists(atPath: scriptPath) else {
            throw LTXError.generationFailed("Preview script not found")
        }
        var args = [
            scriptPath,
            "--prompt", prompt,
            "--model-repo", modelRepo,
            "--temperature", String(temperature),
            "--resources-path", resourcesPath,
        ]
        if let img = sourceImagePath, !img.isEmpty {
            args.append(contentsOf: ["--image", img])
        }
        progressHandler("Loading prompt enhancer (first run may download ~7GB)...")
        let output = try await runPythonScript(executable: python, arguments: args, timeout: 120)
        if let data = output.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            if let enhanced = json["enhanced_prompt"] as? String, !enhanced.isEmpty {
                return enhanced
            }
            if let err = json["error"] as? String {
                throw LTXError.generationFailed(err)
            }
        }
        return nil
    }

    private func runPythonScript(
        executable: String,
        arguments: [String],
        timeout: TimeInterval = 60
    ) async throws -> String {
        try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                let process = Process()
                process.executableURL = URL(fileURLWithPath: executable)
                process.arguments = arguments
                var env: [String: String] = [:]
                let pythonBin = URL(fileURLWithPath: executable).deletingLastPathComponent().path
                env["PATH"] = "\(pythonBin):/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
                env["HOME"] = ProcessInfo.processInfo.environment["HOME"] ?? ""
                env["USER"] = ProcessInfo.processInfo.environment["USER"] ?? ""
                env["TMPDIR"] = ProcessInfo.processInfo.environment["TMPDIR"] ?? "/tmp"
                process.environment = env
                let stdoutPipe = Pipe()
                let stderrPipe = Pipe()
                process.standardOutput = stdoutPipe
                process.standardError = stderrPipe
                do {
                    try process.run()
                    process.waitUntilExit()
                    let outputData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
                    let output = String(data: outputData, encoding: .utf8) ?? ""
                    let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
                    if process.terminationStatus != 0 {
                        let errData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
                        let errStr = String(data: errData, encoding: .utf8) ?? ""
                        continuation.resume(throwing: LTXError.generationFailed(errStr.isEmpty ? "Exit code \(process.terminationStatus)" : errStr))
                    } else {
                        continuation.resume(returning: trimmed)
                    }
                } catch {
                    continuation.resume(throwing: LTXError.generationFailed(error.localizedDescription))
                }
            }
        }
    }
}
