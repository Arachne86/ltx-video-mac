import Foundation
import PythonKit

class PythonEnvironment {
    static let shared = PythonEnvironment()
    
    private(set) var isConfigured = false
    
    private init() {}
    
    func configure() {
        guard !isConfigured else { return }
        
        // Try to find Python from user defaults or common locations
        let pythonPath = UserDefaults.standard.string(forKey: "pythonPath") 
            ?? findPythonPath()
        
        if let path = pythonPath {
            setenv("PYTHON_LIBRARY", path, 1)
            
            // Extract Python home and version from path
            // e.g., /Users/jc/.pyenv/versions/3.12.11/lib/libpython3.12.dylib
            if let pythonHome = path.components(separatedBy: "/lib/libpython").first {
                setenv("PYTHONHOME", pythonHome, 1)
                
                // Set PYTHONPATH to include site-packages
                let sitePackages = "\(pythonHome)/lib/python3.12/site-packages"
                let libPath = "\(pythonHome)/lib/python3.12"
                let pythonPathEnv = "\(sitePackages):\(libPath)"
                setenv("PYTHONPATH", pythonPathEnv, 1)
            }
        }
        
        isConfigured = true
    }
    
    func reconfigure(withPath path: String) {
        setenv("PYTHON_LIBRARY", path, 1)
        
        if let pythonHome = path.components(separatedBy: "/lib/libpython").first {
            setenv("PYTHONHOME", pythonHome, 1)
            
            // Detect Python version from path
            let versionPattern = try? NSRegularExpression(pattern: "libpython(\\d+\\.\\d+)")
            var pythonVersion = "3.12"
            if let match = versionPattern?.firstMatch(in: path, range: NSRange(path.startIndex..., in: path)),
               let range = Range(match.range(at: 1), in: path) {
                pythonVersion = String(path[range])
            }
            
            let sitePackages = "\(pythonHome)/lib/python\(pythonVersion)/site-packages"
            let libPath = "\(pythonHome)/lib/python\(pythonVersion)"
            let pythonPathEnv = "\(sitePackages):\(libPath)"
            setenv("PYTHONPATH", pythonPathEnv, 1)
        }
    }
    
    private func findPythonPath() -> String? {
        let commonPaths = [
            "/Users/jc/.pyenv/versions/3.12.11/lib/libpython3.12.dylib",
            "/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib",
            "/opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib",
            "/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib",
            "/Library/Frameworks/Python.framework/Versions/3.11/lib/libpython3.11.dylib",
            "/Library/Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib"
        ]
        
        for path in commonPaths {
            if FileManager.default.fileExists(atPath: path) {
                return path
            }
        }
        
        return nil
    }
    
    func validatePythonSetup() -> (success: Bool, message: String) {
        // Reconfigure with current saved path
        if let path = UserDefaults.standard.string(forKey: "pythonPath"), !path.isEmpty {
            reconfigure(withPath: path)
        }
        
        do {
            let sys = try Python.import("sys")
            let version = String(sys.version) ?? "unknown"
            
            // Check for required packages
            let requiredPackages = ["torch", "diffusers"]
            var missingPackages: [String] = []
            
            for pkg in requiredPackages {
                do {
                    _ = try Python.import(pkg)
                } catch {
                    missingPackages.append(pkg)
                }
            }
            
            if !missingPackages.isEmpty {
                return (false, "Missing packages: \(missingPackages.joined(separator: ", ")). Run: pip install torch diffusers")
            }
            
            return (true, "Python \(version) configured successfully")
        } catch {
            return (false, "Failed to initialize Python: \(error.localizedDescription)")
        }
    }
}
