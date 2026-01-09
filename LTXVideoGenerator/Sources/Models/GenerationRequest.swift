import Foundation

struct GenerationRequest: Identifiable, Codable, Equatable {
    let id: UUID
    let prompt: String
    let negativePrompt: String
    var parameters: GenerationParameters
    let createdAt: Date
    var status: GenerationStatus
    
    init(
        id: UUID = UUID(),
        prompt: String,
        negativePrompt: String = "",
        parameters: GenerationParameters = .default,
        createdAt: Date = Date(),
        status: GenerationStatus = .pending
    ) {
        self.id = id
        self.prompt = prompt
        self.negativePrompt = negativePrompt
        self.parameters = parameters
        self.createdAt = createdAt
        self.status = status
    }
}

enum GenerationStatus: String, Codable, Equatable {
    case pending
    case processing
    case completed
    case failed
    case cancelled
}

struct GenerationParameters: Codable, Equatable, Hashable {
    var numInferenceSteps: Int
    var guidanceScale: Double
    var width: Int
    var height: Int
    var numFrames: Int
    var fps: Int
    var seed: Int?
    
    // Default uses MPS-safe dimensions (tested working on Apple Silicon)
    static let `default` = GenerationParameters(
        numInferenceSteps: 25,
        guidanceScale: 5.0,
        width: 512,
        height: 320,
        numFrames: 25,
        fps: 24,
        seed: nil
    )
    
    // Standard quality - moderate dimensions
    static let standard = GenerationParameters(
        numInferenceSteps: 40,
        guidanceScale: 5.0,
        width: 640,
        height: 384,
        numFrames: 49,
        fps: 24,
        seed: nil
    )
    
    // High quality - larger dimensions (may have MPS issues on some configs)
    static let highQuality = GenerationParameters(
        numInferenceSteps: 50,
        guidanceScale: 7.0,
        width: 768,
        height: 512,
        numFrames: 65,
        fps: 24,
        seed: nil
    )
    
    var estimatedDuration: String {
        // Rough estimate based on parameters
        let baseTime = Double(numInferenceSteps) * 0.5
        let sizeMultiplier = Double(width * height) / (768.0 * 512.0)
        let frameMultiplier = Double(numFrames) / 97.0
        let totalSeconds = baseTime * sizeMultiplier * frameMultiplier
        
        if totalSeconds < 60 {
            return "\(Int(totalSeconds))s"
        } else {
            let minutes = Int(totalSeconds) / 60
            let seconds = Int(totalSeconds) % 60
            return "\(minutes)m \(seconds)s"
        }
    }
}
