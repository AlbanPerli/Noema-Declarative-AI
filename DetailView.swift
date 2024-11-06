import SwiftUI
struct DetailView: View {
    var item: ItemModel
    var body: some View {
        Text(item.name)
            .font(.title)
        Text(item.description)
            .font(.subheadline)
    }
}
