// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "LTXVideoGenerator",
    platforms: [
        .macOS(.v14)
    ],
    dependencies: [
        .package(url: "https://github.com/pvieito/PythonKit.git", branch: "master")
    ],
    targets: [
        .executableTarget(
            name: "LTXVideoGenerator",
            dependencies: ["PythonKit"],
            path: "Sources"
        )
    ]
)
