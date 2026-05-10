class Route:
    def __init__(self, name, samples):
        self.name = name
        self.samples = samples


menuSample = [
    "Shop có bánh gì?",
    "Cho mình xem menu",
    "Menu hôm nay có gì?",
    "Bên mình bán những loại bánh nào?",
    "Có loại bánh nào?",
    "Có vị nào?",
    "Danh sách bánh của shop",
    "Shop có bánh su không?",
    "Shop có set mini không?",
    "Shop có bánh sinh nhật không?",
    "Có bánh event không?",
    "Cho mình xem các sản phẩm đang bán",
    "Bên Chewy Chewy có món gì?",
    "Có bánh nào mới không?",
    "Có bánh nào bán chạy không?",
    "Shop có những dòng bánh nào?",
]


priceSample = [
    "Giá bánh bao nhiêu?",
    "Bánh chewy bao nhiêu tiền?",
    "Bánh su giá bao nhiêu?",
    "Set mini giá bao nhiêu?",
    "Bao nhiêu một hộp?",
    "Một set bao nhiêu tiền?",
    "Cho mình xin bảng giá",
    "Có bánh dưới 100k không?",
    "Có bánh dưới 200k không?",
    "Bánh nào rẻ nhất?",
    "Bánh nào giá tốt?",
    "Tầm giá bánh bên mình thế nào?",
    "Bánh sinh nhật bao nhiêu?",
    "Bánh vị socola bao nhiêu?",
    "Bánh matcha bao nhiêu?",
    "Bánh dâu bao nhiêu?",
    "Có combo giá bao nhiêu?",
]


recommendSample = [
    "Bánh nào ít ngọt?",
    "Bánh nào ngon nhất?",
    "Bánh nào best seller?",
    "Tư vấn giúp mình một hộp bánh ngon",
    "Mình muốn mua bánh tặng sinh nhật",
    "Mua tặng bạn gái nên chọn bánh nào?",
    "Mua tặng bạn trai nên chọn loại nào?",
    "Mua làm quà nên chọn gì?",
    "Mua cho gia đình nên chọn bánh nào?",
    "Mua cho trẻ em nên chọn bánh nào?",
    "Mua cho 5 người ăn nên chọn loại nào?",
    "Mình thích vị socola thì nên mua gì?",
    "Mình thích vị dâu thì nên mua gì?",
    "Mình thích matcha thì chọn loại nào?",
    "Có loại nào ngọt nhẹ không?",
    "Có loại nào béo béo không?",
    "Có loại nào dễ ăn không?",
    "Có bánh nào hợp tiệc sinh nhật không?",
    "Có bánh nào hợp tiệc công ty không?",
    "Có bánh nào đẹp để tặng không?",
    "Ngân sách 200k nên mua gì?",
    "Ngân sách 300k nên chọn bánh nào?",
    "Mình chưa biết chọn gì, tư vấn giúp mình",
    "dòng bánh nào ít ngọt",
    "gợi ý bánh sinh nhật",
    "mình thích vị matcha",
    "tư vấn bánh",
    "bánh nào ngon",
    "dòng bánh nào ít ngọt",
    "bánh nào ít ngọt",
    "mẫu bánh ít ngọt",
    "gợi ý bánh ít ngọt",
    "mình thích ít ngọt",
    "vị nào ít ngọt",
    "bánh ngọt nhẹ",
    "bánh cho người không thích ngọt",
    "bánh dễ ăn",
    "bánh thanh nhẹ",
    "bánh khoảng 10 người ăn",
    "bánh cho 10 người",
    "gợi ý bánh cho nhóm đông",
    "bánh sinh nhật cho gia đình",
    "bánh cho tiệc",
    "bánh cho nhiều người ăn",
    "bánh cho công ty",
    "bánh cho 8 người",
    "bánh cho 15 người",
    "bánh cho 20 người",
    "bánh cho trẻ em",
    "bánh cho cặp đôi",
    "bánh cho người yêu",

]


orderSample = [
    "Cho mình đặt bánh",
    "Mình muốn đặt bánh",
    "Mình muốn order",
    "Cho mình order",
    "Chốt đơn giúp mình",
    "Mình muốn chốt đơn",
    "Mình lấy 1 hộp",
    "Mình lấy 2 hộp",
    "Cho mình lấy 1 set",
    "Cho mình đặt 2 hộp vị socola",
    "Đặt cho mình set này",
    "Mình muốn mua bánh",
    "Mình mua 1 hộp",
    "Shop giao cho mình 2 set nhé",
    "Mình đặt giao hôm nay được không?",
    "Cho mình đặt bánh sinh nhật",
    "Cho mình đặt set mini",
    "Mình muốn mua vị matcha",
    "Mình muốn mua vị dâu",
    "Mình muốn mua vị chocolate",
    "Đơn của mình gồm 2 hộp",
    "Mình lấy bánh này nha",
    "Shop lên đơn giúp mình",
]


deliverySample = [
    "Có ship quận 7 không?",
    "Có ship quận 1 không?",
    "Shop có giao hàng không?",
    "Phí ship bao nhiêu?",
    "Bao lâu thì giao tới?",
    "Có giao trong ngày không?",
    "Có ship nội thành không?",
    "Có giao ngoài thành phố không?",
    "Ship tỉnh không?",
    "Giao hàng thế nào?",
    "Giao trong bao lâu?",
    "Mình ở Thủ Đức có giao không?",
    "Mình ở Gò Vấp có ship không?",
    "Mình ở Bình Thạnh có giao không?",
    "Mình ở quận 10 có giao không?",
    "Có freeship không?",
    "Đặt bao nhiêu thì được freeship?",
    "Shop giao bằng app nào?",
    "Có giao hỏa tốc không?",
    "Mình muốn nhận bánh hôm nay được không?",
    "Tôi muốn mua trực tiếp thì tới đâu?",
    "Shop ở đâu?",
    "Cửa hàng ở đâu?",
    "Địa chỉ cửa hàng",
    "Có chi nhánh nào gần đây không?",
    "Mua trực tiếp ở đâu?",
    "Tôi muốn ghé cửa hàng",
    "Shop có cửa hàng offline không?",
    "Có thể tới mua trực tiếp không?",
    "Cho mình địa chỉ shop",
]


storeSample = [
    "Cửa hàng ở đâu?",
    "Shop ở đâu vậy?",
    "Địa chỉ shop ở đâu?",
    "Chi nhánh ở đâu?",
    "Shop có bán trực tiếp không?",
    "Có cửa hàng offline không?",
    "Có mua tại cửa hàng được không?",
    "Mình muốn tới mua trực tiếp",
    "Shop mở cửa mấy giờ?",
    "Shop đóng cửa mấy giờ?",
    "Giờ hoạt động của shop?",
    "Có chi nhánh ở quận 1 không?",
    "Có chi nhánh ở quận 7 không?",
    "Có chi nhánh ở Thủ Đức không?",
    "Có chi nhánh ở Gò Vấp không?",
    "Chi nhánh gần mình nhất ở đâu?",
    "Mình ở quận 10 thì mua ở đâu gần?",
    "Chewy Chewy có mấy cửa hàng?",
    "Cho mình xin danh sách cửa hàng",
]


storageSample = [
    "Bánh để được bao lâu?",
    "Cách bảo quản bánh",
    "Bảo quản bánh như thế nào?",
    "Có cần để tủ lạnh không?",
    "Bánh dùng trong mấy ngày?",
    "Để ngoài được không?",
    "Để qua đêm được không?",
    "Bánh có mau hỏng không?",
    "Hạn dùng của bánh là bao lâu?",
    "Bánh mua về để tủ lạnh được không?",
    "Bánh để nhiệt độ phòng được không?",
    "Bánh nên ăn trong ngày không?",
    "Mua bánh trước một ngày được không?",
    "Bánh có cần giữ lạnh khi giao không?",
    "Bánh su bảo quản sao?",
    "Set mini bảo quản sao?",
]


supportSample = [
    "Mình chưa nhận được bánh",
    "Đơn hàng bị giao sai",
    "Đơn bị thiếu bánh",
    "Bánh bị lỗi",
    "Bánh bị hư",
    "Bánh bị móp",
    "Mình muốn khiếu nại",
    "Shop kiểm tra đơn giúp mình",
    "Mình muốn đổi đơn",
    "Mình muốn hủy đơn",
    "Mình muốn hoàn tiền",
    "Shipper chưa giao tới",
    "Mình đặt rồi mà chưa thấy giao",
    "Shop kiểm tra giúp mình đơn hàng",
    "Đơn của mình đang ở đâu?",
    "Mình nhận sai vị bánh",
    "Bánh giao không đúng mẫu",
    "Mình cần hỗ trợ đơn hàng",
]


chitchatSample = [
    "Xin chào",
    "Chào shop",
    "Hello",
    "Hi",
    "Hi shop",
    "Alo",
    "Shop ơi",
    "Bạn ơi",
    "Có ai không?",
    "Cảm ơn",
    "Thanks",
    "Thank you",
    "Ok shop",
    "Dạ ok",
    "Tạm biệt",
    "Bye",
    "Hẹn gặp lại",
    "Bạn là ai?",
    "Bạn làm gì?",
    "Bạn có thể giúp gì?",
]


menuRoute = Route("menu", menuSample)
priceRoute = Route("price", priceSample)
recommendRoute = Route("recommend", recommendSample)
orderRoute = Route("order", orderSample)
deliveryRoute = Route("delivery", deliverySample)
storeRoute = Route("store", storeSample)
storageRoute = Route("storage", storageSample)
supportRoute = Route("support", supportSample)
chitchatRoute = Route("chitchat", chitchatSample)


routes = [
    menuRoute,
    priceRoute,
    recommendRoute,
    orderRoute,
    deliveryRoute,
    storeRoute,
    storageRoute,
    supportRoute,
    chitchatRoute,
]