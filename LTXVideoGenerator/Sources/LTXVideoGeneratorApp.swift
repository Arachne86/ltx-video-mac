import SwiftUI
import PythonKit

@main
struct LTXVideoGeneratorApp: App {
    
    init() {
        // Configure Python environment
        PythonEnvironment.shared.configure()
    }
    
    var body: some Scene {
        WindowGroup {
            RootView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: false))
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
        
        Settings {
            SettingsRootView()
        }
    }
}

struct RootView: View {
    @StateObject private var historyManager: HistoryManager
    @StateObject private var presetManager: PresetManager
    @StateObject private var generationService: GenerationService
    @State private var showPythonSetupAlert = false
    @State private var hasCheckedPython = false
    
    init() {
        let history = HistoryManager()
        _historyManager = StateObject(wrappedValue: history)
        _presetManager = StateObject(wrappedValue: PresetManager())
        _generationService = StateObject(wrappedValue: GenerationService(historyManager: history))
    }
    
    private var isPythonConfigured: Bool {
        let path = UserDefaults.standard.string(forKey: "pythonPath")
        return path != nil && !path!.isEmpty && FileManager.default.fileExists(atPath: path!)
    }
    
    var body: some View {
        ContentView()
            .environmentObject(historyManager)
            .environmentObject(presetManager)
            .environmentObject(generationService)
            .task {
                historyManager.loadInitialData()
                presetManager.loadInitialData()
                
                // Check Python configuration on first launch
                if !hasCheckedPython {
                    hasCheckedPython = true
                    if !isPythonConfigured {
                        // Small delay to let the UI settle
                        try? await Task.sleep(nanoseconds: 500_000_000)
                        showPythonSetupAlert = true
                    }
                }
            }
            .alert("Python Setup Required", isPresented: $showPythonSetupAlert) {
                Button("Open Preferences") {
                    NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
                }
                Button("Later", role: .cancel) {}
            } message: {
                Text("LTX Video Generator requires Python with PyTorch and diffusers installed.\n\nPlease set your Python path in Preferences to start generating videos.")
            }
    }
}

struct SettingsRootView: View {
    var body: some View {
        PreferencesView()
    }
}
