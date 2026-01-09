import Foundation

struct Preset: Identifiable, Codable, Equatable, Hashable {
    let id: UUID
    var name: String
    var parameters: GenerationParameters
    var isBuiltIn: Bool
    let createdAt: Date
    
    init(
        id: UUID = UUID(),
        name: String,
        parameters: GenerationParameters,
        isBuiltIn: Bool = false,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.parameters = parameters
        self.isBuiltIn = isBuiltIn
        self.createdAt = createdAt
    }
    
    // All presets use MPS-safe dimensions (divisible by 32, moderate sizes)
    static let builtInPresets: [Preset] = [
        Preset(
            name: "Fast Preview",
            parameters: .default,
            isBuiltIn: true
        ),
        Preset(
            name: "Standard",
            parameters: .standard,
            isBuiltIn: true
        ),
        Preset(
            name: "High Quality",
            parameters: .highQuality,
            isBuiltIn: true
        ),
        Preset(
            name: "Portrait",
            parameters: GenerationParameters(
                numInferenceSteps: 35,
                guidanceScale: 5.0,
                width: 384,
                height: 640,
                numFrames: 41,
                fps: 24,
                seed: nil
            ),
            isBuiltIn: true
        ),
        Preset(
            name: "Square",
            parameters: GenerationParameters(
                numInferenceSteps: 35,
                guidanceScale: 5.0,
                width: 512,
                height: 512,
                numFrames: 41,
                fps: 24,
                seed: nil
            ),
            isBuiltIn: true
        ),
        Preset(
            name: "Cinematic 21:9",
            parameters: GenerationParameters(
                numInferenceSteps: 40,
                guidanceScale: 6.0,
                width: 768,
                height: 320,
                numFrames: 49,
                fps: 24,
                seed: nil
            ),
            isBuiltIn: true
        )
    ]
}
