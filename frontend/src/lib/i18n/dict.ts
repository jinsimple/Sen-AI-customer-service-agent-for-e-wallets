// UI dictionary. Every key MUST have both `vi` and `en` — enforced by the `Entry` type, so a missing
// translation fails `tsc`. Keep keys grouped by screen; `{name}` placeholders are interpolated by
// `translate()`; `<b>…</b>` / `<strong>…</strong>` are rendered by `rich()` where used.
type Entry = { vi: string; en: string };

export const DICT = {
  // ── language switch ───────────────────────────────────────────────────────────────────────────
  "lang.switchLabel": { vi: "Ngôn ngữ giao diện", en: "Interface language" },

  // ── app shell ─────────────────────────────────────────────────────────────────────────────────
  "app.brand": { vi: "Sen — Trợ lý CSKH ví điện tử", en: "Sen — E-wallet customer support assistant" },
  "app.metaTitle": { vi: "Sen — Trợ lý CSKH ví điện tử", en: "Sen — E-wallet customer support assistant" },
  "app.metaDescription": {
    vi: "FIN-05 — AI Agent CSKH xử lý khiếu nại giao dịch ví điện tử",
    en: "FIN-05 — an AI agent that helps e-wallet support teams investigate transaction complaints",
  },
  "app.footer": { vi: "FIN-05 · P-226 — AI 20K Build Phase Cohort 3", en: "FIN-05 · P-226 — AI 20K Build Phase Cohort 3" },

  // ── roles ─────────────────────────────────────────────────────────────────────────────────────
  "role.customer": { vi: "Khách hàng", en: "Customer" },
  "role.cskh": { vi: "CSKH", en: "Support agent" },
  "role.supervisor": { vi: "Sếp", en: "Supervisor" },
  "role.partner_admin": { vi: "Đối tác ví", en: "Wallet partner" },

  // ── navigation tabs ───────────────────────────────────────────────────────────────────────────
  "nav.chat": { vi: "Trợ lý AI", en: "AI assistant" },
  "nav.queue": { vi: "Hàng chờ", en: "Queue" },
  "nav.policyLookup": { vi: "Tra cứu chính sách", en: "Policy lookup" },
  "nav.report": { vi: "Báo cáo vận hành", en: "Operations report" },
  "nav.approve": { vi: "Phê duyệt", en: "Approvals" },
  "nav.agentsOnline": { vi: "CSKH online", en: "Agents online" },
  "nav.ticketAdmin": { vi: "Quản lý ticket", en: "Ticket management" },
  "nav.knowledge": { vi: "Chính sách & FAQ", en: "Policies & FAQ" },

  // ── user menu ─────────────────────────────────────────────────────────────────────────────────
  "menu.lightMode": { vi: "Chế độ sáng", en: "Light mode" },
  "menu.darkMode": { vi: "Chế độ tối", en: "Dark mode" },
  "menu.logout": { vi: "Đăng xuất", en: "Log out" },

  // ── environment badge ─────────────────────────────────────────────────────────────────────────
  "env.unreachable": { vi: "KHÔNG NỐI ĐƯỢC BACKEND", en: "BACKEND UNREACHABLE" },
  "env.unreachableTitle": {
    vi: "Không gọi được {backend}/health — kiểm tra backend đã chạy chưa.",
    en: "Could not reach {backend}/health — check that the backend is running.",
  },
  "env.title": {
    vi: "Môi trường: {env}\nDatabase: {kind} / {name}\nBackend: {backend}\n\nHai cửa sổ trình duyệt PHẢI hiện cùng một nhãn. Khác nhãn = đang ở hai hệ thống khác nhau với hai database khác nhau (xem ADR-009).",
    en: "Environment: {env}\nDatabase: {kind} / {name}\nBackend: {backend}\n\nTwo browser windows MUST show the same label. Different labels = two different systems with two different databases (see ADR-009).",
  },

  // ── login (shared) ────────────────────────────────────────────────────────────────────────────
  "login.phone": { vi: "Số điện thoại", en: "Phone number" },
  "login.password": { vi: "Mật khẩu", en: "Password" },
  "login.submit": { vi: "Đăng nhập", en: "Log in" },
  "login.submitting": { vi: "Đang đăng nhập…", en: "Logging in…" },
  "login.errWrong": { vi: "Số điện thoại hoặc mật khẩu không đúng.", en: "Incorrect phone number or password." },
  "login.errTimeout": { vi: "Máy chủ phản hồi quá lâu (>10s) — thử lại giúp mình nhé.", en: "The server took too long to respond (>10s) — please try again." },
  "login.errNetwork": {
    vi: "Không kết nối được máy chủ — kiểm tra backend đã chạy chưa (make run).",
    en: "Could not reach the server — check that the backend is running (make run).",
  },

  // ── customer login ────────────────────────────────────────────────────────────────────────────
  "clogin.tagline": {
    vi: "Điều tra khiếu nại giao dịch bằng AI, quyết định cuối cùng luôn thuộc về con người.",
    en: "AI investigates transaction complaints; the final decision always belongs to a human.",
  },
  "clogin.trustMasking": {
    vi: "Thông tin của người khác trong giao dịch được che trước khi hiển thị. Phần suy luận của mô hình đi qua nhà cung cấp đã khai báo, và hệ thống có sẵn cơ chế chuyển đổi nhà cung cấp.",
    en: "Other people's details in a transaction are masked before display. Model inference goes through a declared provider, and the system can switch providers without a rebuild.",
  },
  "common.neverAsk": {
    vi: "Sen không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của bạn.",
    en: "Sen will never ask for your wallet password or a transaction OTP.",
  },
  "clogin.trustAudit": {
    vi: "Mọi phê duyệt hoàn tiền được ghi log — truy vết được ai, khi nào, căn cứ gì.",
    en: "Every refund approval is logged — who, when and on what evidence is always traceable.",
  },
  "clogin.hello": { vi: "Chào bạn 👋", en: "Hello 👋" },
  "clogin.sub": { vi: "Đăng nhập để tiếp tục với trợ lý AI của ví — vài giây thôi.", en: "Log in to continue with the wallet's AI assistant — it only takes a few seconds." },
  "clogin.demoNote": { vi: "tài khoản khách hàng bên dưới dùng mật khẩu", en: "the customer account below uses the password" },
  "clogin.quickLogin": { vi: "Đăng nhập nhanh (demo)", en: "Quick login (demo)" },
  "clogin.quickCustomer": { vi: "Khách hàng — {phone}", en: "Customer — {phone}" },

  // ── staff login ───────────────────────────────────────────────────────────────────────────────
  "slogin.title": { vi: "Đăng nhập nội bộ", en: "Staff login" },
  "slogin.sub": { vi: "Dành cho nhân viên CSKH, sếp phê duyệt và đối tác ví.", en: "For support agents, approving supervisors and wallet partners." },

  // ── public "for customers" page ───────────────────────────────────────────────────────────────
  "fc.eyebrow": { vi: "Sen · Ví điện tử", en: "Sen · E-wallet" },
  "fc.h1": {
    vi: "Sen là trợ lý AI của tổng đài ví. Sen không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của bạn.",
    en: "Sen is the wallet help desk's AI assistant. Sen will never ask for your wallet password or a transaction OTP.",
  },
  "fc.lead": {
    vi: "Khi bạn gặp sự cố — bị trừ tiền hai lần, tiền chưa tới nơi, chuyển nhầm người — Sen tra cứu giao dịch và chuẩn bị hồ sơ để nhân viên xử lý.",
    en: "When something goes wrong — charged twice, money not arriving, sent to the wrong person — Sen looks up the transaction and prepares a case for a staff member to handle.",
  },
  "fc.leadStrong": { vi: "Sen không tự quyết định bất cứ điều gì về tiền của bạn.", en: "Sen never decides anything about your money on its own." },
  "fc.neverH2": { vi: "Ba điều Sen không bao giờ hỏi bạn", en: "Three things Sen will never ask you for" },
  "fc.never1": { vi: "<b>Mật khẩu ví của bạn.</b> Không bao giờ, không vì lý do gì.", en: "<b>Your wallet password.</b> Never, for any reason." },
  "fc.never2": {
    vi: "<b>Mã OTP giao dịch.</b> Sen có thể xin mã xác thực <i>phiên hỗ trợ</i> để mở tra cứu — đó là mã khác, và Sen sẽ nói rõ. Mã OTP để <i>duyệt một giao dịch</i> thì không bao giờ.",
    en: "<b>A transaction OTP.</b> Sen may ask for a verification code for the <i>support session</i> to unlock lookups — that is a different code, and Sen will say so. An OTP that <i>approves a transaction</i>, never.",
  },
  "fc.never3": {
    vi: "<b>Chuyển tiền đi đâu đó.</b> Sen không bao giờ yêu cầu bạn chuyển tiền để “xác minh”, “mở khoá” hay “nhận lại tiền”.",
    en: "<b>Sending money anywhere.</b> Sen will never ask you to transfer money to “verify”, “unlock” or “get your money back”.",
  },
  "fc.warn": {
    vi: "<b>Nếu ai đó tự xưng là Sen mà hỏi một trong ba điều trên — đó là lừa đảo.</b> Dừng lại. Đừng đưa. Gọi tổng đài của ví bạn đang dùng.",
    en: "<b>If anyone claiming to be Sen asks for any of these three things — it is a scam.</b> Stop. Don't share it. Call your wallet's official help line.",
  },
  "fc.afterH2": { vi: "Sau khi bạn nhắn, chuyện gì xảy ra", en: "What happens after you send a message" },
  "fc.after1": {
    vi: "<b>1 · Sen tra cứu.</b> Nó tìm giao dịch bạn nói tới và đối chiếu với quy định. Nếu không tìm ra, nó nói thẳng là không tìm ra — nó không đoán.",
    en: "<b>1 · Sen looks it up.</b> It finds the transaction you mean and checks it against the rules. If it can't find it, it says so plainly — it doesn't guess.",
  },
  "fc.after2": {
    vi: "<b>2 · Một nhân viên thật đọc hồ sơ.</b> Không phải máy đọc. Người đọc, và người đó thấy được từng bước Sen đã tra.",
    en: "<b>2 · A real staff member reads the case.</b> Not a machine. A person, who can see every lookup step Sen took.",
  },
  "fc.after3": {
    vi: "<b>3 · Người có thẩm quyền quyết định.</b> Mọi việc liên quan tới tiền — hoàn tiền, điều chỉnh số dư — chỉ người này quyết được. Sen không quyết. Nhân viên tiếp nhận cũng không quyết.",
    en: "<b>3 · Someone with authority decides.</b> Anything involving money — refunds, balance adjustments — only this person can decide. Sen doesn't. The agent who took the case doesn't either.",
  },
  "fc.track": { vi: "Bạn theo dõi được hồ sơ của mình đang ở bước nào.", en: "You can follow which step your case is at." },
  "fc.canH3": { vi: "Sen giúp được gì", en: "What Sen can help with" },
  "fc.can1": { vi: "Tra cứu giao dịch của bạn và cho biết trạng thái thật của nó", en: "Look up your transaction and tell you its real status" },
  "fc.can2": { vi: "Giải thích quy định áp dụng cho trường hợp của bạn", en: "Explain the rules that apply to your case" },
  "fc.can3": { vi: "Mở hồ sơ khiếu nại và chuyển tới nhân viên", en: "Open a complaint case and pass it to a staff member" },
  "fc.can4": { vi: "Gọi một nhân viên thật vào cuộc trò chuyện khi bạn cần", en: "Bring a real staff member into the conversation when you need one" },
  "fc.cantH3": { vi: "Sen không làm gì", en: "What Sen doesn't do" },
  "fc.cant1": { vi: "Không hoàn tiền, không điều chỉnh số dư — Sen không có quyền đó", en: "No refunds, no balance adjustments — Sen has no such authority" },
  "fc.cant2": { vi: "Không kết luận ai đúng ai sai, không kết luận có gian lận hay không", en: "No verdicts on who is right, and no conclusions about fraud" },
  "fc.cant3": { vi: "Không khoá ví của bạn", en: "Never locks your wallet" },
  "fc.cant4": {
    vi: "Không trả lời khi không tra được — trường hợp đó Sen nói thẳng, thay vì đoán một câu nghe cho xuôi",
    en: "No answers it couldn't look up — in that case Sen says so, instead of guessing something that merely sounds right",
  },
  "fc.wrongH2": { vi: "Nếu bạn thấy có gì đó không ổn", en: "If something doesn't feel right" },
  "fc.wrong1": { vi: "Bạn có thể yêu cầu nói chuyện với nhân viên thật bất cứ lúc nào — chỉ cần nhắn.", en: "You can ask to talk to a real staff member at any time — just say so." },
  "fc.wrong2": {
    vi: "Nếu ai đó liên hệ bạn, tự xưng là Sen hoặc là tổng đài, và hỏi mật khẩu, mã OTP giao dịch, hoặc bảo bạn chuyển tiền: <b>đó không phải chúng tôi.</b> Dừng lại và gọi tổng đài của ví bạn đang dùng.",
    en: "If anyone contacts you claiming to be Sen or the help desk, and asks for your password or a transaction OTP, or tells you to transfer money: <b>that is not us.</b> Stop and call your wallet's official help line.",
  },
  "fc.footerBrand": { vi: "Sen · Trợ lý CSKH ví điện tử", en: "Sen · E-wallet support assistant" },
  "fc.footerDim": {
    vi: "Sen hiện là sản phẩm mẫu, chạy trên dữ liệu mô phỏng và chưa phục vụ khách hàng thật của ví nào.",
    en: "Sen is currently a prototype running on simulated data; it does not serve real customers of any wallet.",
  },

  // ── landing page ("/") ────────────────────────────────────────────────────────────────────────
  "lp.brand": { vi: "Sen · FIN-05", en: "Sen · FIN-05" },
  "lp.login": { vi: "Đăng nhập", en: "Log in" },
  "lp.heroH1": {
    vi: "Khiếu nại giao dịch, điều tra trong vài phút — quyết định vẫn thuộc về con người",
    en: "Transaction complaints investigated in minutes — the decision still belongs to a human",
  },
  "lp.heroLead": {
    vi: "Sen là trợ lý AI cho đội chăm sóc khách hàng ví điện tử. Nó tra cứu giao dịch, đối chiếu chính sách và chuẩn bị hồ sơ có dẫn chứng. <strong>Người duyệt vẫn là người.</strong>",
    en: "Sen is an AI assistant for e-wallet customer support teams. It looks up transactions, checks them against policy and prepares an evidence-backed case. <strong>The approver is still a person.</strong>",
  },
  "lp.heroCta": { vi: "Dùng thử ngay — tài khoản demo", en: "Try it now — demo account" },
  "lp.triedH2": { vi: "Ngành đã thử hướng kia rồi", en: "The industry has already tried the other way" },
  "lp.tried1": {
    vi: "Năm 2024, một fintech lớn công bố trợ lý AI của họ làm việc của <b>700 nhân viên</b>. Năm 2025, chính lãnh đạo công ty thừa nhận việc lấy chi phí làm tiêu chí đánh giá chủ đạo đã dẫn tới <b>chất lượng thấp hơn</b> — và họ tuyển người thật trở lại.",
    en: "In 2024, a large fintech announced its AI assistant was doing the work of <b>700 employees</b>. In 2025, the company's own leadership admitted that making cost the dominant evaluation criterion had led to <b>lower quality</b> — and they started hiring people back.",
  },
  "lp.tried2": {
    vi: "Sen chọn “AI cộng người” từ đầu. Không phải vì chúng tôi khôn hơn — mà vì với tiền thật của khách hàng, không có lựa chọn nào khác.",
    en: "Sen chose “AI plus people” from day one. Not because we are smarter — but because with customers' real money, there is no other option.",
  },
  "lp.tried3": {
    vi: "<b>Và chúng tôi ép nó bằng kiến trúc, không bằng chính sách.</b> Nguyên tắc người đề xuất không được là người duyệt nằm ở tầng ràng buộc của cơ sở dữ liệu. Một chính sách đảo được bằng một cuộc họp. Cái này thì không.",
    en: "<b>And we enforce it with architecture, not policy.</b> The rule that the proposer can never be the approver lives in the database's constraint layer. A policy can be reversed in a meeting. This can't.",
  },
  "lp.nightH2": { vi: "Sự cố tiền bạc không đợi giờ hành chính", en: "Money problems don't wait for office hours" },
  "lp.nightQuote": {
    vi: "“Khách chuyển nhầm lúc 2 giờ sáng, và không liên hệ được tổng đài.”",
    en: "“A customer sent money to the wrong person at 2 a.m., and couldn't reach the help desk.”",
  },
  "lp.nightBody": {
    vi: "Hạ tầng thanh toán chạy 24/7. Nhu cầu hỗ trợ cũng vậy — hai trong ba khung giờ cao điểm của người mua sắm nằm ngoài giờ hành chính. Nhưng đồng hồ pháp lý cho tra soát khiếu nại thì đếm từ <b>ngày tiếp nhận</b>, không đếm từ ngày đội trực đi làm.",
    en: "Payment infrastructure runs 24/7. So does the need for support — two of shoppers' three peak periods fall outside office hours. But the legal clock for investigating a complaint starts on <b>the day it is received</b>, not the day the on-call team comes in.",
  },
  "lp.p1": {
    vi: "<b>Không bịa số.</b> Mỗi con số agent nói ra đều truy ngược được tới một lần tra cứu có thật. Không tra được, nó nói thẳng là không tra được.",
    en: "<b>No made-up numbers.</b> Every figure the agent states traces back to a real lookup. If it can't look something up, it says so plainly.",
  },
  "lp.p2": {
    vi: "<b>Không vượt quyền.</b> Agent gọi công cụ dưới danh nghĩa khách hàng, không hơn. Không có đường nào để AI tự hoàn tiền.",
    en: "<b>No overreach.</b> The agent calls tools with the customer's permissions, nothing more. There is no path for the AI to issue a refund on its own.",
  },
  "lp.p3": {
    vi: "<b>Không hỏi thứ không được hỏi.</b> Sen không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của khách hàng.",
    en: "<b>Never asks what it must not ask.</b> Sen never asks for a customer's wallet password or transaction OTP.",
  },
  "lp.flowH2": { vi: "Bốn bước xử lý một khiếu nại", en: "Four steps to handle a complaint" },
  "lp.flow1b": { vi: "① Khách gửi khiếu nại", en: "① Customer files a complaint" },
  "lp.flow1s": { vi: "Nhắn như nói chuyện bình thường", en: "Writes as they would talk" },
  "lp.flow2b": { vi: "② AI điều tra", en: "② AI investigates" },
  "lp.flow2s": { vi: "Tra giao dịch, đối chiếu chính sách, dựng hồ sơ có dẫn chứng", en: "Looks up transactions, checks policy, builds an evidence-backed case" },
  "lp.flow3b": { vi: "③ CSKH kiểm tra và trình", en: "③ Support agent reviews and submits" },
  "lp.flow3s": { vi: "Người thật đọc hồ sơ, xác minh, rồi trình lên", en: "A real person reads the case, verifies it, then submits it" },
  "lp.flow4b": { vi: "④ Sếp duyệt", en: "④ Supervisor approves" },
  "lp.flow4s": { vi: "Chỉ cấp duyệt mới ra được quyết định cuối", en: "Only the approval level can make the final decision" },
  "lp.figAlt": {
    vi: "Màn hình chat của khách hàng: agent tự đưa cảnh báo chống lừa đảo, cột phải hiện bảng trạng thái hồ sơ khiếu nại",
    en: "Customer chat screen: the agent volunteers an anti-scam warning; the right column shows the complaint case status board",
  },
  "lp.figCaption": {
    vi: "Một ca thật. Bảng trạng thái bên phải cho thấy hồ sơ đang chờ CSKH tiếp nhận, và bước “Chờ Sếp phê duyệt” vẫn còn ở phía trước. Cảnh báo lừa đảo bên trái do trợ lý tự đưa ra — không ai hỏi.",
    en: "A real case (screenshot of the Vietnamese UI). The status board on the right shows the case waiting for a support agent, with the “awaiting supervisor approval” step still ahead. The scam warning on the left was volunteered by the assistant — nobody asked for it.",
  },
  "lp.costH2": { vi: "Chi phí người tăng theo giờ phủ. Chi phí máy thì không.", en: "Human cost grows with hours covered. Machine cost doesn't." },
  "lp.cost1": {
    vi: "Phủ hỗ trợ 24/7 cần <b>168 giờ mỗi tuần</b>. Với ca 40 giờ, đó là hơn bốn người trước khi tính phép, ốm và đào tạo — và <b>hơn một nửa số giờ ấy</b> rơi vào ban đêm hoặc cuối tuần, nơi lương phải cộng phụ trội theo luật.",
    en: "24/7 support coverage needs <b>168 hours a week</b>. With 40-hour shifts that is more than four people before leave, sickness and training — and <b>more than half of those hours</b> fall at night or on weekends, where the law requires premium pay.",
  },
  "lp.cost2": { vi: "Sen không có đường chi phí đó. Hai giờ sáng và hai giờ chiều tốn như nhau.", en: "Sen has no such cost curve. 2 a.m. costs the same as 2 p.m." },
  "lp.costH3": { vi: "Và nó không tiêu tiền cho việc không cần tới mô hình", en: "And it doesn't spend money where no model is needed" },
  "lp.cost3": {
    vi: "Một câu chào hỏi không cần tới AI. Sen nhận ra bằng luật cứng và trả lời trong <b>0,06 giây</b>, tốn <b>0 token</b>. Cùng câu đó nếu đẩy qua mô hình đầy đủ: <b>6.216 token</b> và <b>8,70 giây</b>.",
    en: "A greeting doesn't need AI. Sen recognises it with hard rules and answers in <b>0.06 seconds</b>, using <b>0 tokens</b>. The same message pushed through the full model: <b>6,216 tokens</b> and <b>8.70 seconds</b>.",
  },
  "lp.cost4": {
    vi: "Đây không phải “mô hình thông minh hơn nên rẻ hơn”. Đây là <b>không gọi mô hình</b>. Cơ chế tất định — nó không phụ thuộc hôm nay mô hình hành xử ra sao.",
    en: "This isn't “a smarter model, so it's cheaper”. It is <b>not calling a model at all</b>. A deterministic mechanism — independent of how the model happens to behave today.",
  },
  "lp.statsH2": { vi: "Không phải lời hứa — là con số đếm được", en: "Not promises — countable numbers" },
  "lp.statRoutes": {
    vi: "{n} đường vào hệ thống. Mọi đường đều kiểm quyền theo vai, không có cửa sau.",
    en: "{n} entry points into the system. Every one is role-checked; there is no back door.",
  },
  "lp.statTools": {
    vi: "Năm công cụ AI được phép gọi. Năm công cụ bị cấm tuyệt đối — chúng không tồn tại trong hàm dựng công cụ.",
    en: "Five tools the AI may call. Five tools strictly forbidden — they don't exist in the tool factory.",
  },
  "lp.statCases": { vi: "Ca đánh giá chất lượng, chia {sets} bộ riêng biệt.", en: "Quality-evaluation cases, split into {sets} separate datasets." },
  "lp.statSealed": {
    vi: "Trong số đó, 60 ca được niêm phong từ đầu và chưa ai chạy lần nào — để bộ đo không bị tối ưu ngược. Chúng chỉ được mở một lần, gần cuối.",
    en: "Of those, 60 cases were sealed from the start and never run — so the yardstick can't be over-fitted. They are opened only once, near the end.",
  },
  "lp.statZero": { vi: "Quyết định hoàn tiền AI được phép tự ra.", en: "Refund decisions the AI is allowed to make on its own." },
  "lp.statsNote": { vi: "Đếm ngày {date} — đổi contract thì đếm lại.", en: "Counted on {date} — recount whenever the contracts change." },
  "lp.legal1": {
    vi: "Thiết kế theo khung pháp lý hiện hành cho trung gian thanh toán tại Việt Nam — <b>NĐ 52/2024</b> và <b>TT 40/2024</b>. Dữ liệu cá nhân xử lý theo <b>Luật 91/2025/QH15</b>. Thông tin bên thứ ba trong giao dịch được che trước khi hiển thị.",
    en: "Designed against Vietnam's current legal framework for payment intermediaries — <b>Decree 52/2024</b> and <b>Circular 40/2024</b>. Personal data is handled under <b>Law 91/2025/QH15</b>. Third-party details in transactions are masked before display.",
  },
  "lp.legal2": {
    vi: "Hệ thống chạy trong vùng hạ tầng do ví kiểm soát. Phần suy luận của mô hình đi qua nhà cung cấp đã khai báo, và hệ thống có sẵn cơ chế chuyển đổi nhà cung cấp mà không phải dựng lại.",
    en: "The system runs inside infrastructure the wallet controls. Model inference goes through a declared provider, and the system can switch providers without being rebuilt.",
  },
  "lp.legal3": {
    vi: "Kho tài liệu chính sách của đối tác được mã hoá khi lưu. Kho tìm kiếm chỉ giữ mã tham chiếu, không giữ nội dung tài liệu.",
    en: "The partner's policy document store is encrypted at rest. The search index holds only reference IDs, never document content.",
  },
  "lp.footerBrand": { vi: "Sen · Trợ lý CSKH ví điện tử", en: "Sen · E-wallet support assistant" },
  "lp.footerCta": { vi: "Dùng thử tài khoản demo", en: "Try the demo account" },

  // ── shared bits ───────────────────────────────────────────────────────────────────────────────
  "common.loading": { vi: "Đang tải…", en: "Loading…" },
  "common.cancel": { vi: "Huỷ", en: "Cancel" },
  "common.confirm": { vi: "Xác nhận", en: "Confirm" },
  "common.verifying": { vi: "Đang xác thực...", en: "Verifying..." },
  "time.justNow": { vi: "vừa xong", en: "just now" },
  "time.minutesAgo": { vi: "{n} phút trước", en: "{n} min ago" },
  "time.hoursAgo": { vi: "{n} giờ trước", en: "{n} h ago" },
  "time.daysAgo": { vi: "{n} ngày trước", en: "{n} d ago" },

  // ── notification bell ─────────────────────────────────────────────────────────────────────────
  "notif.title": { vi: "Thông báo", en: "Notifications" },
  "notif.unreadAria": { vi: "{n} thông báo chưa đọc", en: "{n} unread notifications" },
  "notif.markAll": { vi: "Đánh dấu tất cả đã đọc", en: "Mark all as read" },
  "notif.empty": { vi: "Chưa có thông báo nào.", en: "No notifications yet." },

  // ── investigation step ────────────────────────────────────────────────────────────────────────
  "step.showMore": { vi: "Xem thêm {n} dòng", en: "Show {n} more rows" },
  "step.collapse": { vi: "Thu gọn", en: "Collapse" },
  "step.asked": { vi: "Đã hỏi", en: "Query" },
  "step.result": { vi: "Kết quả", en: "Result" },
  "step.blockedOtp": { vi: "Bị chặn — cần xác thực OTP phiên trước khi tra cứu", en: "Blocked — session OTP verification required before lookup" },
  "step.noData": { vi: "Không tra được dữ liệu", en: "Data not available" },
  "step.technical": { vi: "Xem dữ liệu kỹ thuật", en: "Show technical data" },

  // ── wrong-role banner ─────────────────────────────────────────────────────────────────────────
  "wrongRole.customer": { vi: "Khách hàng", en: "Customer" },
  "wrongRole.cskh": { vi: "Nhân viên CSKH", en: "Support agent" },
  "wrongRole.supervisor": { vi: "Cấp duyệt", en: "Supervisor" },
  "wrongRole.partner_admin": { vi: "Đối tác ví", en: "Wallet partner" },
  "wrongRole.loggedInAs": { vi: "Bạn đang đăng nhập bằng tài khoản {role}.", en: "You are logged in as {role}." },
  "wrongRole.thisScreen": {
    vi: "Màn hình này dành cho <strong>{role}</strong>. Nhiều khả năng bạn vừa đăng nhập vai khác ở một tab khác trong cùng trình duyệt — mỗi trình duyệt chỉ giữ được một phiên.",
    en: "This screen is for <strong>{role}</strong>. Most likely you just logged in with another role in a different tab of the same browser — each browser holds only one session.",
  },
  "wrongRole.incognito": {
    vi: "Muốn dùng song song hai vai: mở <strong>cửa sổ ẩn danh</strong> cho vai thứ hai.",
    en: "To use two roles side by side, open a <strong>private/incognito window</strong> for the second role.",
  },
  "wrongRole.back": { vi: "→ Về màn hình của {role}", en: "→ Back to the {role} screen" },

  // ── staff presence ────────────────────────────────────────────────────────────────────────────
  "presence.loadError": { vi: "Không tải được danh sách CSKH", en: "Could not load the support agent list" },
  "presence.title": { vi: "CSKH đang online", en: "Support agents online" },
  "presence.empty": { vi: "Chưa có CSKH nào trong hệ thống.", en: "No support agents in the system yet." },
  "presence.colStaff": { vi: "Nhân viên", en: "Agent" },
  "presence.colStatus": { vi: "Trạng thái", en: "Status" },
  "presence.colTickets": { vi: "Số vé đang xử lý", en: "Tickets in progress" },
  "presence.online": { vi: "Đang online", en: "Online" },
  "presence.offline": { vi: "Offline", en: "Offline" },

  // ── OTP input ─────────────────────────────────────────────────────────────────────────────────
  "otp.needSix": { vi: "Nhập đủ 6 số OTP để tiếp tục.", en: "Enter all 6 OTP digits to continue." },

  // ── approve / reject actions ──────────────────────────────────────────────────────────────────
  "approval.otpRequestFailed": { vi: "Không xin được mã OTP duyệt", en: "Could not request an approval OTP" },
  "approval.approveFailed": { vi: "Duyệt thất bại", en: "Approval failed" },
  "approval.rejectFailed": { vi: "Từ chối thất bại", en: "Rejection failed" },
  "approval.enterOtp": {
    vi: "Nhập mã OTP xác nhận duyệt (còn hiệu lực 10 phút, chỉ dùng được cho đúng đề xuất này):",
    en: "Enter the approval OTP (valid for 10 minutes, usable only for this exact proposal):",
  },
  "approval.demoOtp": { vi: "Mã OTP duyệt (mô phỏng):", en: "Approval OTP (simulated):" },
  "approval.rejectReason": { vi: "Lý do từ chối", en: "Rejection reason" },
  "approval.chooseReason": { vi: "— chọn lý do —", en: "— choose a reason —" },
  "approval.insufficientHint": {
    vi: "Nếu CSKH có thể bổ sung được căn cứ, hãy dùng <b>Yêu cầu điều tra thêm</b> ở màn chi tiết ticket thay vì từ chối — chỉ từ chối khi không thể bổ sung.",
    en: "If the support agent can still supply the evidence, use <b>Request more investigation</b> on the ticket detail screen instead of rejecting — reject only when it cannot be supplied.",
  },
  "approval.confirmReject": { vi: "Xác nhận từ chối", en: "Confirm rejection" },
  "approval.approve": { vi: "Duyệt", en: "Approve" },
  "approval.reject": { vi: "Từ chối", en: "Reject" },

  // ── page eyebrows ─────────────────────────────────────────────────────────────────────────────
  "eyebrow.supervisor": { vi: "Webapp Sếp", en: "Supervisor webapp" },
  "eyebrow.cskh": { vi: "Webapp CSKH", en: "Support webapp" },

  // ── supervisor: staff online / ticket management ──────────────────────────────────────────────
  "cskhOnline.title": { vi: "CSKH online", en: "Support agents online" },
  "cskhOnline.sub": {
    vi: "Ai đang online và đang xử lý bao nhiêu vé — để biết phân bổ việc, không phải để chấm công.",
    en: "Who is online and how many tickets each is handling — for workload balancing, not time tracking.",
  },
  "ticketMgmt.title": { vi: "Quản lý ticket", en: "Ticket management" },
  "ticketMgmt.sub": {
    vi: "Toàn bộ ticket trong hệ thống, không riêng ca đang chờ duyệt — để nắm bức tranh chung.",
    en: "Every ticket in the system, not just the ones awaiting approval — for the big picture.",
  },

  // ── support agent: queue ──────────────────────────────────────────────────────────────────────
  "queue.title": { vi: "Hàng chờ ticket", en: "Ticket queue" },
  "queue.sub": {
    vi: "Lọc/sắp xếp theo trạng thái và ưu tiên để xử lý đúng case cấp bách trước. Case nghi gian lận (tín hiệu FS-06) nổi bật rõ hơn ticket thường.",
    en: "Filter and sort by status and priority to handle the most urgent cases first. Suspected-fraud cases (FS-06 signal) stand out from ordinary tickets.",
  },
  "queue.waitingChats": { vi: "Khách đang chờ chat trực tiếp ({n})", en: "Customers waiting for live chat ({n})" },
  "queue.waitingSince": { vi: "Chờ từ {time}", en: "Waiting since {time}" },
  "queue.openClaim": { vi: "Mở & nhận", en: "Open & claim" },

  // ── policy document / lookup ──────────────────────────────────────────────────────────────────
  "policyDoc.loadError": { vi: "Không tải được tài liệu", en: "Could not load the document" },
  "policyDoc.cantOpen": { vi: "Không mở được tài liệu", en: "Could not open the document" },
  "policyDoc.eyebrow": { vi: "Webapp CSKH · Tài liệu chính sách", en: "Support webapp · Policy document" },
  "policyDoc.noFullText": {
    vi: "Tài liệu này chưa có bản toàn văn để hiển thị — vui lòng dùng đoạn trích ở kết quả tra cứu.",
    en: "This document has no full text to display yet — please use the excerpt from the search results.",
  },
  "policyDoc.sub": {
    vi: "Toàn văn tài liệu — đoạn trích khớp câu tra cứu được tô sáng bên dưới, nếu có.",
    en: "Full document text — the excerpt matching your query is highlighted below, if any.",
  },
  "policyLookup.failed": { vi: "Tra cứu thất bại", en: "Search failed" },
  "policyLookup.eyebrow": { vi: "Webapp CSKH · Tra cứu chính sách", en: "Support webapp · Policy lookup" },
  "policyLookup.title": { vi: "Tra cứu chính sách & FAQ", en: "Policy & FAQ lookup" },
  "policyLookup.sub": {
    vi: "Tìm nhanh nội dung chính sách/FAQ mới nhất do đối tác ví cập nhật — hữu ích khi xử lý ticket cần đối chiếu quy định. Kết quả là đoạn trích nguyên văn, không qua tổng hợp AI.",
    en: "Quickly find the latest policy/FAQ content uploaded by the wallet partner — useful when a ticket needs checking against the rules. Results are verbatim excerpts, not AI summaries.",
  },
  "policyLookup.placeholder": {
    vi: "Vd: phí rút tiền, thời gian hoàn tiền double_charge...",
    en: "e.g. withdrawal fee, double_charge refund time... (policy documents are in Vietnamese)",
  },
  "policyLookup.searching": { vi: "Đang tìm…", en: "Searching…" },
  "policyLookup.search": { vi: "Tìm kiếm", en: "Search" },
  "policyLookup.none": { vi: "Chưa tìm thấy tài liệu chính sách nào khớp với câu hỏi này.", en: "No policy document matches this query yet." },
  "policyLookup.fullText": { vi: "Xem toàn văn ↗", en: "View full text ↗" },

  // ── operations report ─────────────────────────────────────────────────────────────────────────
  "report.noData": { vi: "Chưa có dữ liệu.", en: "No data yet." },
  "report.loadError": { vi: "Không tải được báo cáo", en: "Could not load the report" },
  "report.title": { vi: "Báo cáo vận hành", en: "Operations report" },
  "report.sub": {
    vi: "Số liệu tính trực tiếp từ dữ liệu ticket thật tại thời điểm xem — không phải ước lượng.",
    en: "Figures are computed directly from real ticket data at the time of viewing — not estimates.",
  },
  "report.apply": { vi: "Áp dụng", en: "Apply" },
  "report.cycleTime": { vi: "Thời gian từ tiếp nhận đến phê duyệt (cycle time)", en: "Time from intake to approval (cycle time)" },
  "report.hours": { vi: "{n} giờ", en: "{n} h" },
  "report.basedOn": { vi: "tính trên {n} case đã duyệt", en: "based on {n} approved cases" },
  "report.aht": { vi: "AHT — thời gian người thao tác thật", en: "AHT — actual human handling time" },
  "report.notMeasured": { vi: "Chưa đo được", en: "Not measurable yet" },
  "report.pctApproved": { vi: "% đề xuất của CSKH được sếp duyệt", en: "% of support-agent proposals approved" },
  "report.pctEscalated": { vi: "% escalate", en: "% escalated" },
  "report.total": { vi: "Tổng ticket trong kỳ", en: "Total tickets in period" },
  "report.byType": { vi: "Phân bố theo loại khiếu nại", en: "Breakdown by complaint type" },
  "report.byScope": { vi: "Phân bố theo phạm vi giao dịch", en: "Breakdown by transaction scope" },

  // ── client/server error messages ──────────────────────────────────────────────────────────────
  "err.sessionExpired": { vi: "Phiên làm việc đã hết hạn — mời bạn đăng nhập lại.", en: "Your session has expired — please log in again." },
  "err.timeout": { vi: "Máy chủ phản hồi quá lâu (>{s}s) — thử lại giúp mình nhé.", en: "The server took too long to respond (>{s}s) — please try again." },
  "err.backendTimeout": { vi: "Backend phản hồi quá lâu — thử lại giúp mình nhé.", en: "The backend took too long to respond — please try again." },
  "err.invalid": { vi: "không hợp lệ", en: "invalid" },
  "err.invalidPayload": { vi: "Dữ liệu gửi lên chưa hợp lệ — {detail}", en: "The submitted data is invalid — {detail}" },
  "err.notLoggedIn": { vi: "Chưa đăng nhập", en: "Not logged in" },
  "err.wrongGate": {
    vi: "Tài khoản này không đăng nhập tại đây. Vui lòng dùng cổng dành cho nhân viên.",
    en: "This account can't log in here. Please use the staff login page.",
  },
  "err.loginFailed": { vi: "Đăng nhập thất bại", en: "Login failed" },

  // ── supervisor: approvals ─────────────────────────────────────────────────────────────────────
  "approve.loadError": { vi: "Không tải được hàng chờ phê duyệt", en: "Could not load the approval queue" },
  "approve.title": { vi: "Phê duyệt (HITL)", en: "Approvals (HITL)" },
  "approve.sub": {
    vi: "Đủ căn cứ hiển thị ngay để quyết trong vài giây. Case chạm ngân hàng chỉ có nút tạo yêu cầu tra soát — không bao giờ có đường tắt bỏ qua con người.",
    en: "Enough evidence on screen to decide in seconds. Bank-facing cases only get a button to file an investigation request — there is never a shortcut that bypasses a human.",
  },
  "approve.none": { vi: "Không có đề xuất nào đang chờ duyệt.", en: "No proposals awaiting approval." },
  "approve.internalBadge": { vi: "Nội bộ ví — đủ quyền thực thi trực tiếp", en: "Wallet-internal — can be executed directly" },
  "approve.bankBadge": { vi: "Chạm ngân hàng — chờ đối tác xác nhận", en: "Bank-facing — awaiting partner confirmation" },
  "approve.proposal": { vi: "Đề xuất từ CSKH", en: "Support agent's proposal" },
  "approve.rationale": { vi: "Căn cứ", en: "Rationale" },
  "approve.submittedAt": { vi: "Trình lúc", en: "Submitted at" },
  "approve.bankNote": {
    vi: "Case chạm ngân hàng: quyết định duyệt ở đây ghi log căn cứ, CSKH là người gửi yêu cầu tra soát riêng (xem chi tiết ticket).",
    en: "Bank-facing case: approving here logs the rationale; the support agent files the separate investigation request (see ticket detail).",
  },
  "approve.openDetail": { vi: "Mở chi tiết →", en: "Open detail →" },
  "approve.logTitle": { vi: "Nhật ký hành động phê duyệt", en: "Approval action log" },
  "approve.colTime": { vi: "Thời gian", en: "Time" },
  "approve.colWho": { vi: "Ai", en: "Who" },
  "approve.colAction": { vi: "Hành động", en: "Action" },
  "approve.colTicket": { vi: "Ticket", en: "Ticket" },
  "approve.colRationale": { vi: "Căn cứ", en: "Rationale" },
  "approve.noActions": { vi: "Chưa có hành động nào.", en: "No actions yet." },
  "approve.logNote": {
    vi: "Log không sửa/xoá được bởi người dùng thường — tra cứu được theo ticket_id.",
    en: "The log can't be edited or deleted by regular users — searchable by ticket_id.",
  },

  // ── wallet partner: knowledge base ────────────────────────────────────────────────────────────
  "kb.status.processing": { vi: "Đang xử lý", en: "Processing" },
  "kb.status.indexed": { vi: "Đã lập chỉ mục", en: "Indexed" },
  "kb.status.failed": { vi: "Lỗi", en: "Error" },
  "kb.loadError": { vi: "Không tải được danh sách tài liệu", en: "Could not load the document list" },
  "kb.uploadFailed": { vi: "Upload thất bại", en: "Upload failed" },
  "kb.deleteFailed": { vi: "Xoá thất bại", en: "Delete failed" },
  "kb.eyebrow": { vi: "Webapp Đối tác ví · RAG chính sách/FAQ", en: "Wallet partner webapp · Policy/FAQ RAG" },
  "kb.title": { vi: "Chính sách & FAQ", en: "Policies & FAQ" },
  "kb.sub": {
    vi: "Tài liệu tải lên ở đây được AI agent dùng để trả lời khách hàng và giúp CSKH tra cứu nhanh — hỗ trợ .md/.txt/.pdf/.docx (không hỗ trợ .doc cũ). Nội dung được mã hoá khi lưu trữ.",
    en: "Documents uploaded here are used by the AI agent to answer customers and by support agents for quick lookup — .md/.txt/.pdf/.docx supported (legacy .doc is not). Content is encrypted at rest.",
  },
  "kb.uploadTitle": { vi: "Tải tài liệu mới", en: "Upload a new document" },
  "kb.uploading": { vi: "Đang tải lên…", en: "Uploading…" },
  "kb.upload": { vi: "Tải lên", en: "Upload" },
  "kb.listTitle": { vi: "Tài liệu đã tải lên", en: "Uploaded documents" },
  "kb.colFile": { vi: "Tên file", en: "File name" },
  "kb.colUploader": { vi: "Người tải lên", en: "Uploaded by" },
  "kb.colTime": { vi: "Thời gian", en: "Time" },
  "kb.colStatus": { vi: "Trạng thái", en: "Status" },
  "kb.colChunks": { vi: "Số đoạn", en: "Chunks" },
  "kb.delete": { vi: "Xoá", en: "Delete" },
  "kb.empty": { vi: "Chưa có tài liệu nào.", en: "No documents yet." },

  // ── ticket list (queue + ticket management) ───────────────────────────────────────────────────
  "tls.loadError": { vi: "Không tải được danh sách ticket", en: "Could not load the ticket list" },
  "tls.claimError": { vi: "Không nhận được vé", en: "Could not claim the ticket" },
  "tls.filters": { vi: "Bộ lọc", en: "Filters" },
  "tls.type": { vi: "Loại KN", en: "Type" },
  "tls.scope": { vi: "Phạm vi", en: "Scope" },
  "tls.priority": { vi: "Ưu tiên", en: "Priority" },
  "tls.status": { vi: "Trạng thái", en: "Status" },
  "tls.all": { vi: "Tất cả", en: "All" },
  "tls.slaFrom": { vi: "SLA từ", en: "SLA from" },
  "tls.slaTo": { vi: "SLA đến", en: "SLA to" },
  "tls.clearFilters": { vi: "Xoá bộ lọc", en: "Clear filters" },
  "tls.filterNote": {
    vi: "Bộ lọc ở trên áp dụng trên TOÀN BỘ ticket khớp ({total} vé). Hai chip và ô tìm bên dưới CHỈ lọc trong trang đang xem ({page} vé).",
    en: "The filters above apply to ALL matching tickets ({total}). The two chips and the search box below filter ONLY the current page ({page} tickets).",
  },
  "tls.chipPartner": { vi: "Chờ đối tác NH (trang này)", en: "Awaiting bank partner (this page)" },
  "tls.chipHandoff": { vi: "Khách yêu cầu người thật (trang này)", en: "Customer asked for a human (this page)" },
  "tls.searchPlaceholder": { vi: "Tìm theo mã ticket, mã khiếu nại, tên khách (trang này)...", en: "Search by ticket ID, complaint ID, customer name (this page)..." },
  "tls.colNo": { vi: "STT", en: "#" },
  "tls.colTicket": { vi: "Mã ticket", en: "Ticket ID" },
  "tls.colCustomer": { vi: "Khách hàng", en: "Customer" },
  "tls.colUpdated": { vi: "Cập nhật", en: "Updated" },
  "tls.colActions": { vi: "Thao tác", en: "Actions" },
  "tls.handoffBadge": { vi: "Yêu cầu người thật", en: "Wants a human" },
  "tls.claiming": { vi: "Đang nhận…", en: "Claiming…" },
  "tls.claim": { vi: "Nhận vé", en: "Claim" },
  "tls.claimed": { vi: "Đã nhận", en: "Claimed" },
  "tls.noMatch": { vi: "Không có ticket nào khớp bộ lọc.", en: "No tickets match the filters." },
  "tls.prev": { vi: "← Trước", en: "← Previous" },
  "tls.next": { vi: "Sau →", en: "Next →" },
  "tls.pageInfo": { vi: "Trang {page}/{pages} — tổng {total} vé khớp bộ lọc", en: "Page {page}/{pages} — {total} tickets match the filters" },
  "tls.pageSize": { vi: "Số dòng/trang", en: "Rows per page" },

  // ── live chat panel ───────────────────────────────────────────────────────────────────────────
  "live.openError": { vi: "Không mở được phiên chat trực tiếp.", en: "Could not open the live chat session." },
  "live.claimedByOther": { vi: "Phiên chat này vừa có chuyên viên khác nhận.", en: "Another agent has just claimed this chat session." },
  "live.connecting": { vi: "Đang kết nối...", en: "Connecting..." },
  "live.connected": { vi: "Đã kết nối", en: "Connected" },
  "live.disconnected": { vi: "Mất kết nối", en: "Disconnected" },
  "live.connError": { vi: "Lỗi kết nối", en: "Connection error" },
  "live.withCustomer": { vi: "Chat trực tiếp với khách", en: "Live chat with customer" },
  "live.withAgent": { vi: "Chat trực tiếp với CSKH", en: "Live chat with support" },
  "live.aiContext": { vi: "Ngữ cảnh AI đã điều tra:", en: "AI investigation context:" },
  "live.undetermined": { vi: "chưa xác định", en: "not determined" },
  "live.phone": { vi: "SĐT:", en: "Phone:" },
  "live.ended": {
    vi: "Phiên chat đã kết thúc — đây là lịch sử. Nếu cần hỗ trợ thêm, liên hệ khách qua số điện thoại ở trên.",
    en: "The chat has ended — this is the history. For further help, contact the customer at the phone number above.",
  },
  "live.claim": { vi: "Nhận phiên chat này", en: "Claim this chat" },
  "live.end": { vi: "Kết thúc chat", en: "End chat" },
  "live.claimToReply": { vi: "Nhận phiên chat để bắt đầu trả lời", en: "Claim the chat to start replying" },
  "live.typeMessage": { vi: "Nhập tin nhắn...", en: "Type a message..." },
  "live.send": { vi: "Gửi", en: "Send" },
  "live.rate": { vi: "Đánh giá chất lượng hỗ trợ:", en: "Rate the support you received:" },
  "live.thanks": { vi: "Cảm ơn bạn đã đánh giá!", en: "Thanks for your rating!" },

  // ── customer chat ─────────────────────────────────────────────────────────────────────────────
  "chat.cstatus.investigating": { vi: "Đang xử lý", en: "In progress" },
  "chat.cstatus.resolved": { vi: "Đã giải quyết", en: "Resolved" },
  "chat.cstatus.rejected": { vi: "Đã từ chối", en: "Rejected" },
  "chat.verifyNow": { vi: "Xác thực ngay", en: "Verify now" },
  "chat.greeting": {
    vi: "Chào bạn, mình là Sen — trợ lý AI của ví. Mình có thể hỗ trợ bạn những thông tin về ví điện tử, truy vấn các giao dịch và những vấn đề liên quan đến chuyển tiền. Bạn có thể gõ trực tiếp câu hỏi, hoặc bấm \"Báo lỗi giao dịch này\" ở một giao dịch cụ thể bên trái.",
    en: "Hi, I'm Sen — the wallet's AI assistant. I can help with e-wallet information, transaction lookups and money-transfer issues. Type your question, or click \"Report this transaction\" on a specific transaction on the left. (Note: the assistant itself replies in Vietnamese — the product's market language; this interface toggle translates the screens, not the conversation.)",
  },
  "chat.liveEnded": { vi: "Phiên chat trực tiếp đã kết thúc. Bạn có thể tiếp tục hỏi Sen.", en: "The live chat has ended. You can keep asking Sen." },
  "chat.otpRequestFailed": { vi: "Không xin được mã OTP lúc này, bạn thử lại giúp mình nhé.", en: "Couldn't get an OTP right now — please try again." },
  "chat.complaintLabel": { vi: "{label} — giao dịch {id}", en: "{label} — transaction {id}" },
  "chat.needOtpFor": {
    vi: "Mình hiểu bạn đang lo vì {label} — để bảo vệ tài khoản của bạn, mình cần xác thực nhanh trước khi tra cứu nhé.",
    en: "I understand you're worried about \"{label}\" — to protect your account, I need a quick verification before looking it up.",
  },
  "chat.otpFailed": { vi: "Xác thực thất bại, thử lại.", en: "Verification failed, please try again." },
  "chat.otpOkLookup": { vi: "Xác thực thành công — để mình tra ngay giúp bạn.", en: "Verified — let me look that up for you now." },
  "chat.otpOkContinue": { vi: "Xác thực thành công — bạn tiếp tục hỏi mình nhé.", en: "Verified — go ahead with your question." },
  "chat.whichProblem": { vi: "Bạn muốn báo vấn đề gì với giao dịch {amount} lúc {time} này?", en: "What's the problem with this {amount} transaction at {time}?" },
  "chat.source": { vi: "nguồn: {tools}", en: "source: {tools}" },
  "chat.reverifyOtp": { vi: "Để tiếp tục thao tác này, mình cần bạn xác thực lại OTP phiên làm việc nhé.", en: "To continue, please verify your session OTP again." },
  "chat.needOtpSensitive": {
    vi: "Mình vừa cần tra thông tin liên quan tới giao dịch/tài khoản của bạn — xác thực nhanh OTP phiên làm việc để tiếp tục nhé.",
    en: "I need to look up information about your transaction/account — please verify with a session OTP to continue.",
  },
  "chat.errorPrefix": { vi: "Có lỗi: {msg}", en: "Error: {msg}" },
  "chat.connectError": { vi: "Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé.", en: "Couldn't reach the assistant — please try again." },
  "chat.eyebrow": { vi: "Trợ lý AI cho khách hàng", en: "Customer AI assistant" },
  "chat.title": { vi: "Trợ lý AI", en: "AI assistant" },
  "chat.sub": {
    vi: "Trợ lý AI — Sen tra cứu từ hệ thống trước khi trả lời, và nói rõ khi không tra được. Mọi đề xuất đều có người kiểm trước khi thành quyết định.",
    en: "AI assistant — Sen looks things up in the system before answering, and says so when it can't. Every proposal is checked by a person before it becomes a decision.",
  },
  "chat.liveConnectError": { vi: "Không mở được kết nối chat trực tiếp.", en: "Couldn't open the live chat connection." },
  "chat.retry": { vi: "Thử lại", en: "Retry" },
  "chat.recentTx": { vi: "Giao dịch gần đây", en: "Recent transactions" },
  "chat.otpToSeeTx": { vi: "Xác thực OTP để xem giao dịch gần đây", en: "Verify with OTP to see recent transactions" },
  "chat.noTx": { vi: "Chưa có giao dịch.", en: "No transactions yet." },
  "chat.out": { vi: "Chuyển đi", en: "Sent" },
  "chat.in": { vi: "Nhận vào", en: "Received" },
  "chat.reportTx": { vi: "Báo lỗi giao dịch này", en: "Report this transaction" },
  "chat.complaintHistory": { vi: "Lịch sử khiếu nại của bạn", en: "Your complaint history" },
  "chat.otpToSeeComplaints": { vi: "Xác thực OTP để xem lịch sử khiếu nại", en: "Verify with OTP to see your complaint history" },
  "chat.noComplaints": { vi: "Chưa có khiếu nại nào.", en: "No complaints yet." },
  "chat.botName": { vi: "Sen AI · Trợ lý CSKH", en: "Sen AI · Support assistant" },
  "chat.demoOtp": { vi: "Mã OTP phiên làm việc (mô phỏng — gửi tới {phone}):", en: "Session OTP (simulated — sent to {phone}):" },
  "chat.typeMessage": { vi: "Nhập tin nhắn...", en: "Type a message..." },
  "chat.pickOption": { vi: "Chọn một lựa chọn phía trên để tiếp tục", en: "Pick one of the options above to continue" },
  "chat.sendAria": { vi: "Gửi tin nhắn", en: "Send message" },
  "chat.demoData": {
    vi: "Bản demo dùng dữ liệu mô phỏng — vui lòng <strong>không nhập thông tin cá nhân thật</strong>. Nội dung chat được xử lý bởi AI của nhà cung cấp nước ngoài.",
    en: "This demo uses simulated data — please <strong>don't enter real personal information</strong>. Chat content is processed by a foreign AI provider.",
  },
  "chat.statusTitle": { vi: "Trạng thái", en: "Status" },
  "chat.noRequest": { vi: "Chưa có yêu cầu nào trong phiên này.", en: "No requests in this session yet." },
  "chat.stepIntake": { vi: "Tiếp nhận & xác thực", en: "Intake & verification" },
  "chat.stepInvestigate": { vi: "Tra cứu & điều tra", en: "Lookup & investigation" },
  "chat.stepAwaitAgent": { vi: "Chờ CSKH tiếp nhận", en: "Awaiting support agent" },
  "chat.urgent": { vi: "khẩn", en: "urgent" },
  "chat.stepAwaitSupervisor": { vi: "Chờ Sếp phê duyệt", en: "Awaiting supervisor approval" },
  "chat.stepDone": { vi: "Hoàn tất", en: "Done" },
  "chat.liveTitle": { vi: "Chat trực tiếp CSKH", en: "Live chat with support" },

  // ── ticket detail ─────────────────────────────────────────────────────────────────────────────
  "td.loadError": { vi: "Không tải được ticket", en: "Could not load the ticket" },
  "td.submittedOk": { vi: "Đã trình sếp — chờ phê duyệt.", en: "Submitted to the supervisor — awaiting approval." },
  "td.submitFailed": { vi: "Trình sếp thất bại", en: "Submission failed" },
  "td.needMoreInfoOk": { vi: "Đã chuyển ticket sang trạng thái cần điều tra thêm.", en: "Ticket moved to \"needs more investigation\"." },
  "td.actionFailed": { vi: "Thao tác thất bại", en: "Action failed" },
  "td.bankRequestOk": { vi: "Đã gửi yêu cầu tra soát tới ngân hàng đối tác.", en: "Investigation request sent to the partner bank." },
  "td.bankRequestFailed": { vi: "Gửi yêu cầu thất bại", en: "Sending the request failed" },
  "td.backToApprove": { vi: "Phê duyệt", en: "Approvals" },
  "td.backToQueue": { vi: "Hàng chờ", en: "Queue" },
  "td.backTo": { vi: "Quay lại {where}", en: "Back to {where}" },
  "td.critical": { vi: "Khẩn cấp", en: "Critical" },
  "td.investigationLog": { vi: "Nhật ký điều tra", en: "Investigation log" },
  "td.investigationLogSub": { vi: "Mỗi bước: tool đã gọi, input, kết quả, ghi chú AI, thời gian.", en: "Each step: tool called, input, result, AI note, time." },
  "td.noSteps": { vi: "Chưa có bước điều tra nào được ghi cho hồ sơ này.", en: "No investigation steps recorded for this case yet." },
  "td.routingSignal": { vi: "Tín hiệu định tuyến — KHÔNG PHẢI kết luận gian lận", en: "Routing signal — NOT a fraud conclusion" },
  "td.fs06Note": {
    vi: "<b>FS-06</b> (rút sạch sau bất thường xác thực) là tín hiệu DUY NHẤT kích hoạt escalate tự động trong phạm vi MVP (PRD §5) — dù badge phía trên hiện mã nào khác. Các mã khác được ghi lại (kế thừa từ đặc tả gốc 12 tín hiệu) nhưng KHÔNG ảnh hưởng định tuyến hiện tại. Gắn cờ <b>không</b> tự động khoá ví.",
    en: "<b>FS-06</b> (full drain after an authentication anomaly) is the ONLY signal that triggers automatic escalation in the MVP scope (PRD §5) — whatever other code the badge above shows. Other codes are logged (inherited from the original 12-signal spec) but do NOT affect current routing. Flagging a signal does <b>not</b> automatically lock the wallet.",
  },
  "td.conversationTitle": { vi: "Hội thoại với trợ lý", en: "Conversation with the assistant" },
  "td.piiFilterNote": {
    vi: "Bản ghi tự động từ hệ thống lọc thông tin cá nhân — một số câu khách gõ có thể hiện thành nhãn dạng [TÊN_NGƯỜI]/[ĐỊA_ĐIỂM] thay vì nguyên văn nếu bộ lọc nhận nhầm, kể cả với các câu nói chuyện thông thường (không riêng dữ liệu nhạy cảm). Đây là giới hạn đã biết của bộ lọc tại thời điểm ghi, không phải khách thực sự gõ như vậy.",
    en: "Automatically recorded by the PII-scrubbing filter — some customer text may show up as [PERSON_NAME]/[LOCATION] placeholders instead of the original wording when the filter over-triggers, even on ordinary conversational text (not only sensitive data). This is a known limitation of the filter at the time of recording, not what the customer actually typed.",
  },
  "td.handoffMismatch": {
    vi: "Vé này có bàn giao (lúc {time}) nhưng hội thoại không ghi lại đúng thời điểm khách yêu cầu gặp người thật — thường do vé được mở qua nhánh chờ quá lâu chứ không phải khách bấm yêu cầu. Không vẽ được vạch phân cách, nhưng toàn bộ hội thoại dưới đây vẫn đầy đủ.",
    en: "This ticket was handed off (at {time}) but the transcript doesn't record exactly when the customer asked for a human — usually because the ticket opened through the \"waited too long\" branch rather than an explicit request. The handoff marker can't be placed, but the full conversation below is intact.",
  },
  "td.customer": { vi: "Khách", en: "Customer" },
  "td.bot": { vi: "Bot", en: "Bot" },
  "td.basedOnLookup": { vi: "dựa trên dữ liệu tra được", en: "based on looked-up data" },
  "td.handoffMarker": { vi: "— khách yêu cầu gặp người thật tại đây —", en: "— customer asked for a human here —" },
  "td.txInfo": { vi: "Thông tin giao dịch", en: "Transaction info" },
  "td.txNotFound": { vi: "Khách không tra ra được giao dịch (case not_found).", en: "The customer's transaction could not be found (not_found case)." },
  "td.txLoading": { vi: "Đang tra cứu…", en: "Looking up…" },
  "td.txNotFoundById": { vi: "Không tìm thấy giao dịch {id}.", en: "Transaction {id} not found." },
  "td.txId": { vi: "Mã giao dịch", en: "Transaction ID" },
  "td.amount": { vi: "Số tiền", en: "Amount" },
  "td.status": { vi: "Trạng thái", en: "Status" },
  "td.recipient": { vi: "Người nhận", en: "Recipient" },
  "td.pdpaMasked": { vi: "Đã che một phần theo PDPA (Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP).", en: "Partially masked under PDPA (Law 91/2025/QH15, Decree 356/2025/ND-CP)." },
  "td.bankInvestigation": { vi: "Tra soát ngân hàng đối tác", en: "Partner bank investigation" },
  "td.bankInvestigationSub": {
    vi: "Case chạm ngân hàng — chỉ có nút tạo yêu cầu tra soát, không có nút duyệt hoàn tiền trực tiếp.",
    en: "Bank-facing case — only a button to file an investigation request; no button to approve a direct refund.",
  },
  "td.bankRequestSent": { vi: "Đã gửi yêu cầu tra soát — xem trạng thái ở SLA/partner_wait_status.", en: "Investigation request sent — see status under SLA/partner_wait_status." },
  "td.bankReasonLabel": { vi: "Lý do tra soát", en: "Investigation reason" },
  "td.sendBankRequest": { vi: "Gửi yêu cầu tra soát", en: "Send investigation request" },
  "td.yourActions": { vi: "Hành động của bạn (CSKH)", en: "Your actions (support agent)" },
  "td.noSelfApprove": { vi: "Không có đường nào để tự duyệt hoàn tiền.", en: "There is no path to self-approve a refund." },
  "td.proposedAction": { vi: "Hướng xử lý đề xuất", en: "Proposed resolution" },
  "td.amountOptional": { vi: "Số tiền (nếu có)", en: "Amount (if any)" },
  "td.amountMismatch": {
    vi: "⚠ Khác số tiền giao dịch ({amount}) — kiểm tra lại nếu đây không phải hoàn một phần có chủ đích.",
    en: "⚠ Differs from the transaction amount ({amount}) — double-check unless this is an intentional partial refund.",
  },
  "td.rationale": { vi: "Căn cứ", en: "Rationale" },
  "td.submitToSupervisor": { vi: "Trình sếp", en: "Submit to supervisor" },
  "td.requestMoreInfo": { vi: "Yêu cầu điều tra thêm", en: "Request more investigation" },
  "td.outOfAuthority": { vi: "Ngoài thẩm quyền của bạn — chỉ Sếp mới có quyền duyệt hoàn tiền.", en: "Outside your authority — only the supervisor can approve a refund." },
  "td.approveRefund": { vi: "Duyệt hoàn tiền", en: "Approve refund" },
  "td.approvalDecision": { vi: "Quyết định phê duyệt", en: "Approval decision" },
  "td.noPending": { vi: "Ticket này không có đề xuất nào đang chờ duyệt.", en: "This ticket has no proposals awaiting approval." },
  "td.proposal": { vi: "Đề xuất", en: "Proposal" },
  "td.submittedProposals": { vi: "Đề xuất đã trình", en: "Submitted proposals" },
} satisfies Record<string, Entry>;

export type DictKey = keyof typeof DICT;
