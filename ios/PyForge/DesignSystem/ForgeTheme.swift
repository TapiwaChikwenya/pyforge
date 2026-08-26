import SwiftUI

enum ForgeTheme {
    static let ember = Color(red: 1.00, green: 0.36, blue: 0.10)
    static let emberLight = Color(red: 1.00, green: 0.64, blue: 0.30)
    static let coral = Color(red: 1.00, green: 0.45, blue: 0.28)
    static let midnight = Color(red: 0.03, green: 0.05, blue: 0.12)
    static let indigo = Color(red: 0.08, green: 0.11, blue: 0.26)
    static let steel = Color(red: 0.50, green: 0.55, blue: 0.69)
    static let canvas = Color(red: 0.965, green: 0.955, blue: 0.925)
    static let canvasDark = Color(red: 0.025, green: 0.035, blue: 0.075)
    static let success = Color(red: 0.12, green: 0.66, blue: 0.42)
    static let codeBackground = Color(red: 0.025, green: 0.035, blue: 0.075)

    static let accent = ember
    static let ink = midnight

    static let emberGradient = LinearGradient(
        colors: [emberLight, ember, coral],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let midnightGradient = LinearGradient(
        colors: [indigo, midnight],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

struct ForgeBackground: View {
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        ZStack {
            (colorScheme == .dark ? ForgeTheme.canvasDark : ForgeTheme.canvas)
                .ignoresSafeArea()

            Circle()
                .fill(ForgeTheme.ember.opacity(colorScheme == .dark ? 0.11 : 0.08))
                .frame(width: 280, height: 280)
                .blur(radius: 70)
                .offset(x: 170, y: -290)

            Circle()
                .fill(Color.indigo.opacity(colorScheme == .dark ? 0.18 : 0.07))
                .frame(width: 320, height: 320)
                .blur(radius: 85)
                .offset(x: -190, y: 350)
        }
        .accessibilityHidden(true)
    }
}

struct ForgePanelModifier: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme
    let cornerRadius: CGFloat

    func body(content: Content) -> some View {
        content
            .background(
                colorScheme == .dark ? Color.white.opacity(0.065) : Color.white.opacity(0.78),
                in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            )
            .overlay {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(
                        colorScheme == .dark ? Color.white.opacity(0.09) : Color.white.opacity(0.92),
                        lineWidth: 1
                    )
            }
            .shadow(color: ForgeTheme.midnight.opacity(colorScheme == .dark ? 0.24 : 0.08), radius: 18, y: 8)
    }
}

extension View {
    func forgePanel(cornerRadius: CGFloat = 20) -> some View {
        modifier(ForgePanelModifier(cornerRadius: cornerRadius))
    }
}

struct ForgeWordmark: View {
    var compact = false

    var body: some View {
        HStack(spacing: compact ? 8 : 10) {
            Image("BrandMark")
                .resizable()
                .scaledToFill()
                .frame(width: compact ? 30 : 38, height: compact ? 30 : 38)
                .clipShape(RoundedRectangle(cornerRadius: compact ? 8 : 10, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: compact ? 8 : 10, style: .continuous)
                        .stroke(Color.white.opacity(0.16), lineWidth: 0.5)
                }

            VStack(alignment: .leading, spacing: -1) {
                Text("PyForge")
                    .font(compact ? .headline.weight(.black) : .title3.weight(.black))
                if !compact {
                    Text("BUILD · RUN · MASTER")
                        .font(.system(size: 8, weight: .bold, design: .rounded))
                        .tracking(1.3)
                        .foregroundStyle(ForgeTheme.ember)
                }
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("PyForge")
    }
}

struct ForgeSectionTitle: View {
    let eyebrow: String?
    let title: String
    let detail: String?

    init(_ title: String, eyebrow: String? = nil, detail: String? = nil) {
        self.title = title
        self.eyebrow = eyebrow
        self.detail = detail
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            if let eyebrow {
                Text(eyebrow.uppercased())
                    .font(.caption2.bold())
                    .tracking(1.2)
                    .foregroundStyle(ForgeTheme.ember)
            }
            Text(title)
                .font(.title2.weight(.black))
            if let detail {
                Text(detail)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityAddTraits(.isHeader)
    }
}

struct TagView: View {
    let text: String
    var emphasized = false

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .lineLimit(1)
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .foregroundStyle(emphasized ? ForgeTheme.ember : .secondary)
            .background(
                emphasized ? ForgeTheme.ember.opacity(0.12) : Color.secondary.opacity(0.10),
                in: Capsule()
            )
            .overlay {
                if emphasized {
                    Capsule().stroke(ForgeTheme.ember.opacity(0.25), lineWidth: 0.7)
                }
            }
    }
}

struct ProgressRing: View {
    let progress: Double
    var size: CGFloat = 72

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.white.opacity(0.12), lineWidth: size * 0.09)
            Circle()
                .trim(from: 0, to: max(0, min(progress, 1)))
                .stroke(ForgeTheme.emberGradient, style: StrokeStyle(lineWidth: size * 0.09, lineCap: .round))
                .rotationEffect(.degrees(-90))
            Text("\(Int(progress * 100))%")
                .font(.system(size: size * 0.22, weight: .black, design: .rounded))
                .monospacedDigit()
                .foregroundStyle(.white)
        }
        .frame(width: size, height: size)
        .accessibilityElement()
        .accessibilityLabel("Overall progress")
        .accessibilityValue("\(Int(progress * 100)) percent")
    }
}

struct ForgeDivider: View {
    var body: some View {
        HStack(spacing: 5) {
            Capsule().fill(ForgeTheme.ember).frame(width: 20, height: 3)
            Capsule().fill(ForgeTheme.ember.opacity(0.45)).frame(width: 7, height: 3)
            Capsule().fill(ForgeTheme.ember.opacity(0.2)).frame(height: 3)
        }
        .accessibilityHidden(true)
    }
}

struct FlowLayout<Data: RandomAccessCollection, Content: View>: View where Data.Element: Hashable {
    let data: Data
    let content: (Data.Element) -> Content

    init(_ data: Data, @ViewBuilder content: @escaping (Data.Element) -> Content) {
        self.data = data
        self.content = content
    }

    var body: some View {
        _FlowLayout(spacing: 6) {
            ForEach(Array(data), id: \.self, content: content)
        }
    }
}

private struct _FlowLayout: Layout {
    let spacing: CGFloat

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 0
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > 0, x + size.width > width {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: width, height: y + rowHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > bounds.minX, x + size.width > bounds.maxX {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}

struct MarkdownText: View {
    private let attributed: AttributedString

    init(_ markdown: String) {
        attributed = (try? AttributedString(
            markdown: markdown,
            options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
        )) ?? AttributedString(markdown)
    }

    var body: some View {
        Text(attributed)
            .font(.body.leading(.loose))
            .textSelection(.enabled)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
