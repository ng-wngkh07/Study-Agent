import Foundation
import Vision

// Local, literal OCR. Confidence is retained as telemetry, never as approval.
do {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.usesCPUOnly = true
    let languages = try request.supportedRecognitionLanguages()
    request.recognitionLanguages = languages.first(where: { $0.hasPrefix("vi-") })
        .map { [$0, "en-US"] } ?? ["en-US"]
    if CommandLine.arguments.count > 1 {
        let handler = VNImageRequestHandler(url: URL(fileURLWithPath: CommandLine.arguments[1]), options: [:])
        try handler.perform([request])
        let lines = (request.results ?? []).compactMap { observation -> [String: Any]? in
            guard let candidate = observation.topCandidates(1).first else { return nil }
            let b = observation.boundingBox
            return ["text": candidate.string, "confidence": candidate.confidence,
                    "bounds": [b.minX, b.minY, b.width, b.height]]
        }
        let payload: [String: Any] = ["success": true, "languages": request.recognitionLanguages,
            "uses_language_correction": false, "cpu_only": true, "lines": lines]
        print(String(data: try JSONSerialization.data(withJSONObject: payload), encoding: .utf8)!)
    } else {
        print(String(data: try JSONSerialization.data(withJSONObject: ["supported_languages": languages]), encoding: .utf8)!)
    }
} catch {
    let data = try! JSONSerialization.data(withJSONObject: ["success": false, "error": String(describing: error)])
    print(String(data: data, encoding: .utf8)!)
    exit(1)
}
