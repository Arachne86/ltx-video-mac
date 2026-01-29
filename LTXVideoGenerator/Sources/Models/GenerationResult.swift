import Foundation

struct GenerationResult: Identifiable, Codable {
    let id: UUID
    let requestId: UUID
    let prompt: String
    let negativePrompt: String
    let voiceoverText: String  // Voiceover narration text (for audio generation)
    let voiceoverSource: String  // "elevenlabs" or "mlx-audio"
    let voiceoverVoice: String   // Voice ID for TTS
    let parameters: GenerationParameters
    let videoPath: String
    let thumbnailPath: String?
    let audioPath: String?       // Path to voiceover audio
    let musicPath: String?       // Path to background music
    let musicGenre: String?      // Music genre used
    let createdAt: Date
    let completedAt: Date
    let duration: TimeInterval
    let seed: Int
    
    var videoURL: URL {
        URL(fileURLWithPath: videoPath)
    }
    
    var thumbnailURL: URL? {
        thumbnailPath.map { URL(fileURLWithPath: $0) }
    }
    
    var audioURL: URL? {
        audioPath.map { URL(fileURLWithPath: $0) }
    }
    
    var musicURL: URL? {
        musicPath.map { URL(fileURLWithPath: $0) }
    }
    
    var hasAudio: Bool {
        audioPath != nil
    }
    
    var hasMusic: Bool {
        musicPath != nil
    }
    
    var formattedDuration: String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        if minutes > 0 {
            return "\(minutes)m \(seconds)s"
        }
        return "\(seconds)s"
    }
    
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: completedAt)
    }
}

extension GenerationResult {
    static func preview() -> GenerationResult {
        GenerationResult(
            id: UUID(),
            requestId: UUID(),
            prompt: "A cinematic shot of a majestic eagle soaring through mountains",
            negativePrompt: "",
            voiceoverText: "",
            voiceoverSource: "mlx-audio",
            voiceoverVoice: "af_heart",
            parameters: .default,
            videoPath: "/tmp/preview.mp4",
            thumbnailPath: nil,
            audioPath: nil,
            musicPath: nil,
            musicGenre: nil,
            createdAt: Date().addingTimeInterval(-120),
            completedAt: Date(),
            duration: 45.5,
            seed: 42
        )
    }
}
