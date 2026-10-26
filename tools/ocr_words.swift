import Foundation
import Vision
import AppKit
// Prints "path<TAB>wordcount<TAB>text" for each image path given.
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("\(path)\t-1\t"); continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .fast
    try? VNImageRequestHandler(cgImage: cg).perform([req])
    let lines = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    let text = lines.joined(separator: " | ")
    let words = text.split(whereSeparator: { $0 == " " }).filter { $0 != "|" }.count
    print("\(path)\t\(words)\t\(text)")
}
