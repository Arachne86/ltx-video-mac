import SwiftUI

struct PromptInputView: View {
    @EnvironmentObject var generationService: GenerationService
    @EnvironmentObject var presetManager: PresetManager
    
    @Binding var prompt: String
    @Binding var negativePrompt: String
    @Binding var parameters: GenerationParameters
    
    @State private var showNegativePrompt = false
    @State private var showCompletedIndicator = false
    @FocusState private var isPromptFocused: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Main prompt
            VStack(alignment: .leading, spacing: 8) {
                Label("Prompt", systemImage: "text.bubble.fill")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                
                TextEditor(text: $prompt)
                    .font(.body)
                    .frame(minHeight: 80, maxHeight: 120)
                    .scrollContentBackground(.hidden)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(nsColor: .controlBackgroundColor))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(isPromptFocused ? Color.accentColor : Color.clear, lineWidth: 2)
                    )
                    .focused($isPromptFocused)
            }
            
            // Negative prompt toggle
            DisclosureGroup(isExpanded: $showNegativePrompt) {
                TextEditor(text: $negativePrompt)
                    .font(.body)
                    .frame(height: 60)
                    .scrollContentBackground(.hidden)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(nsColor: .controlBackgroundColor))
                    )
            } label: {
                Label("Negative Prompt", systemImage: "minus.circle")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            // Quick actions
            HStack(spacing: 12) {
                // Generate button - changes appearance based on state
                if showCompletedIndicator {
                    // Completion state - green button
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                        Text("Complete!")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(.green)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                } else if generationService.currentRequest != nil {
                    // Processing state - shows spinner (when there's an active generation)
                    HStack(spacing: 8) {
                        ProgressView()
                            .controlSize(.small)
                            .tint(.white)
                        Text("Generating...")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(Color.accentColor.opacity(0.7))
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    // Normal state - generate button
                    Button {
                        generateVideo()
                    } label: {
                        Label("Generate", systemImage: "play.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(prompt.isEmpty || generationService.isProcessing)
                }
                
                // Track completion - only when currentRequest goes away (actual generation done)
                Color.clear
                    .frame(width: 0, height: 0)
                    .onChange(of: generationService.currentRequest) { oldRequest, newRequest in
                        // Generation completed when we had a request and now we don't
                        if oldRequest != nil && newRequest == nil && generationService.error == nil {
                            showCompletedIndicator = true
                            DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                                withAnimation {
                                    showCompletedIndicator = false
                                }
                            }
                        }
                    }
                
                // Add to queue button
                Button {
                    addToQueue()
                } label: {
                    Label("Add to Queue", systemImage: "plus.circle")
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                .disabled(prompt.isEmpty)
                
                // Batch button
                Menu {
                    Button("Generate 3 variations") {
                        generateBatch(count: 3)
                    }
                    Button("Generate 5 variations") {
                        generateBatch(count: 5)
                    }
                    Divider()
                    Button("Generate with random seeds...") {
                        // Could show a dialog for count
                        generateBatch(count: 3)
                    }
                } label: {
                    Image(systemName: "square.stack.3d.up")
                }
                .menuStyle(.borderlessButton)
                .frame(width: 44)
            }
            
            // Status
            if generationService.isProcessing {
                HStack(spacing: 12) {
                    ProgressView(value: generationService.progress)
                        .progressViewStyle(.linear)
                    
                    Text(generationService.statusMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
        }
        .padding()
    }
    
    private func generateVideo() {
        let request = GenerationRequest(
            prompt: prompt,
            negativePrompt: negativePrompt,
            parameters: parameters
        )
        generationService.addToQueue(request)
    }
    
    private func addToQueue() {
        let request = GenerationRequest(
            prompt: prompt,
            negativePrompt: negativePrompt,
            parameters: parameters
        )
        generationService.addToQueue(request)
    }
    
    private func generateBatch(count: Int) {
        let requests = (0..<count).map { _ in
            GenerationRequest(
                prompt: prompt,
                negativePrompt: negativePrompt,
                parameters: GenerationParameters(
                    numInferenceSteps: parameters.numInferenceSteps,
                    guidanceScale: parameters.guidanceScale,
                    width: parameters.width,
                    height: parameters.height,
                    numFrames: parameters.numFrames,
                    fps: parameters.fps,
                    seed: Int.random(in: 0..<Int(Int32.max))
                )
            )
        }
        generationService.addBatch(requests)
    }
}

#Preview {
    PromptInputView(
        prompt: .constant("A majestic eagle soaring through mountains"),
        negativePrompt: .constant(""),
        parameters: .constant(.default)
    )
    .environmentObject(GenerationService(historyManager: HistoryManager()))
    .environmentObject(PresetManager())
    .frame(width: 500)
}
