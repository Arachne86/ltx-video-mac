import SwiftUI

struct PreferencesView: View {
    @AppStorage("pythonPath") private var pythonPath = ""
    @AppStorage("outputDirectory") private var outputDirectory = ""
    @AppStorage("autoLoadModel") private var autoLoadModel = false
    @AppStorage("keepCompletedInQueue") private var keepCompletedInQueue = false
    
    @State private var pythonStatus: (success: Bool, message: String)?
    @State private var isValidating = false
    
    var body: some View {
        TabView {
            // General
            Form {
                Section("Python Environment") {
                    HStack {
                        TextField("Python Library Path", text: $pythonPath)
                            .textFieldStyle(.roundedBorder)
                        
                        Button("Browse...") {
                            selectPythonPath()
                        }
                        
                        Button("Detect") {
                            detectPython()
                        }
                    }
                    
                    if let status = pythonStatus {
                        HStack {
                            Image(systemName: status.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                                .foregroundStyle(status.success ? .green : .red)
                            Text(status.message)
                                .font(.caption)
                        }
                    }
                    
                    Button("Validate Python Setup") {
                        validatePython()
                    }
                    .disabled(isValidating)
                    
                    Text("Path to libpython dylib (e.g., /opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Section("Model") {
                    Toggle("Auto-load model on startup", isOn: $autoLoadModel)
                    
                    Text("The LTX-2 model will be downloaded on first use (~4GB)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Section("Storage") {
                    HStack {
                        TextField("Output Directory", text: $outputDirectory)
                            .textFieldStyle(.roundedBorder)
                        
                        Button("Browse...") {
                            selectOutputDirectory()
                        }
                        
                        Button("Open") {
                            openOutputDirectory()
                        }
                    }
                    
                    Text("Leave empty to use default location in Application Support")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .formStyle(.grouped)
            .tabItem {
                Label("General", systemImage: "gear")
            }
            
            // Generation
            Form {
                Section("Queue") {
                    Toggle("Keep completed items in queue", isOn: $keepCompletedInQueue)
                }
                
                Section("Defaults") {
                    Text("Default generation parameters can be set via Presets")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .formStyle(.grouped)
            .tabItem {
                Label("Generation", systemImage: "wand.and.stars")
            }
            
            // About
            VStack(spacing: 20) {
                Image(systemName: "film.stack")
                    .font(.system(size: 64))
                    .foregroundStyle(.blue.gradient)
                
                Text("LTX Video Generator")
                    .font(.title)
                    .bold()
                
                Text("Version 1.0.0")
                    .foregroundStyle(.secondary)
                
                Divider()
                    .frame(width: 200)
                
                VStack(spacing: 8) {
                    Text("Powered by LTX-2 from Lightricks")
                    Link("https://github.com/Lightricks/LTX-Video",
                         destination: URL(string: "https://github.com/Lightricks/LTX-Video")!)
                }
                .font(.caption)
                .foregroundStyle(.secondary)
                
                Spacer()
            }
            .padding(40)
            .tabItem {
                Label("About", systemImage: "info.circle")
            }
        }
        .frame(width: 500, height: 400)
    }
    
    private func selectPythonPath() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.unixExecutable]
        panel.message = "Select Python library (libpython*.dylib)"
        
        if panel.runModal() == .OK, let url = panel.url {
            pythonPath = url.path
        }
    }
    
    private func selectOutputDirectory() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.canCreateDirectories = true
        
        if panel.runModal() == .OK, let url = panel.url {
            outputDirectory = url.path
        }
    }
    
    private func openOutputDirectory() {
        let path = outputDirectory.isEmpty
            ? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
                .appendingPathComponent("LTXVideoGenerator/Videos").path
            : outputDirectory
        
        NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: path)
    }
    
    private func detectPython() {
        let commonPaths = [
            "/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib",
            "/opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib",
            "/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib",
            "/Library/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib"
        ]
        
        for path in commonPaths {
            if FileManager.default.fileExists(atPath: path) {
                pythonPath = path
                pythonStatus = (true, "Detected Python at \(path)")
                return
            }
        }
        
        pythonStatus = (false, "Could not auto-detect Python. Please select manually.")
    }
    
    private func validatePython() {
        isValidating = true
        pythonStatus = nil
        
        Task.detached {
            // Re-configure with new path
            if !pythonPath.isEmpty {
                PythonEnvironment.shared.reconfigure(withPath: pythonPath)
            }
            
            let result = PythonEnvironment.shared.validatePythonSetup()
            
            await MainActor.run {
                pythonStatus = result
                isValidating = false
            }
        }
    }
}

#Preview {
    PreferencesView()
}
