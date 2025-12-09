# 🎮 Discord Word Chain Bot - Nối Từ

- 🏆 **Hệ thống điểm và xếp hạng**: Leaderboard toàn server
- 💡 **Gợi ý (Hint)**: Tiêu tốn 10 điểm
- ⏭️ **Bỏ lượt (Pass)**: Tiêu tốn 20 điểm
- 🔥 **Bonus điểm**: +5 điểm cho từ dài (>10 ký tự)
- 📈 **Thống kê chi tiết**: Xem stats cá nhân và toàn server

### 🎨 Giao Diện Đẹp

- 🌈 **Rich Embeds**: Sử dụng Discord embeds với màu sắc rực rỡ
- 😀 **Emoji đẹp**: Sử dụng Unicode emojis cho mọi phản hồi
- ⚡ **Phản hồi nhanh**: Bot phản hồi tức thì với animation đẹp mắt

## 🚀 Cài Đặt

### Yêu Cầu

- Python 3.8+
- pip (Python package manager)
- Discord Bot Token ([Tạo bot tại đây](https://discord.com/developers/applications))

### Bước 1: Clone Repository

```bash
git clone <your-repo-url>
cd Noi-Tu
```

### Bước 2: Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu Hình

1. Tạo file `.env` từ template:

```bash
cp .env.example .env
```

2. Mở file `.env` và thêm Discord bot token của bạn:

```env
DISCORD_TOKEN=your_bot_token_here
```

### Bước 4: Mở Rộng Danh Sách Từ (Tùy Chọn)

Thêm nhiều từ hơn vào các file:

- `data/words_vi.txt` - Từ Tiếng Việt
- `data/words_en.txt` - Từ Tiếng Anh

**Lưu ý**: Hiện tại chỉ có danh sách từ mẫu. Để bot hoạt động tốt hơn, bạn nên thêm nhiều từ hơn vào các file này!

### Bước 4: Test API (Tùy chọn nhưng khuyến nghị)

```bash
python test_api.py
```

Nếu thấy `✅ All tests completed!` → API hoạt động tốt!

### Bước 5: Chạy Bot

```bash
python bot.py
```

## 📖 Hướng Dẫn Sử Dụng

### Lệnh Game

- `/start-wordchain [ngôn_ngữ]` - Bắt đầu game (vi hoặc en)
- `/stop-wordchain` - Kết thúc game hiện tại
- `/status` - Xem trạng thái game
- `/challenge-bot [ngôn_ngữ]` - Thách đấu bot 1vs1

### Lệnh Hỗ Trợ

- `/hint` - Nhận gợi ý chữ cái tiếp theo (10 điểm)
- `/pass` - Bỏ lượt không bị trừ điểm (20 điểm)

### Lệnh Thống Kê

- `/leaderboard` - Xem bảng xếp hạng top 10
- `/stats [user]` - Xem thống kê cá nhân

### Lệnh Admin

- `/add-points <user> <points>` - Thêm điểm cho người chơi
- `/reset-stats [user]` - Reset thống kê
- `/help` - Xem hướng dẫn chi tiết

## 🎮 Cách Chơi

1. **Bắt đầu game**: Gõ `/start-wordchain` trong kênh text
2. **Nối từ**: Gửi từ bắt đầu bằng chữ cái cuối của từ trước
   - Ví dụ: `cat` → `tree` → `egg` → `game`
3. **Thời gian**: Bạn có 30 giây để trả lời
4. **Từ duy nhất**: Mỗi từ chỉ được dùng 1 lần trong game
5. **Kiếm điểm**:
   - +1 điểm cho từ đúng
   - +5 điểm cho từ dài (>10 ký tự)
   - -2 điểm cho từ sai hoặc hết giờ

## 🌟 Quy Tắc Đặc Biệt cho Tiếng Việt

Với Tiếng Việt, bot hỗ trợ nối theo **âm tiết**:

- Từ trước: "cái bàn" → Chữ cuối: **"b"** (từ âm tiết "bàn")
- Từ tiếp: "bút" hoặc "bánh" đều được

## ⚙️ Cấu Hình Tùy Chỉnh

Chỉnh sửa file `config.py` hoặc `.env` để thay đổi:

- `TURN_TIMEOUT` - Thời gian mỗi lượt (mặc định: 30s)
- `POINTS_CORRECT` - Điểm cho từ đúng (mặc định: 1)
- `POINTS_LONG_WORD` - Điểm bonus từ dài (mặc định: 5)
- `POINTS_WRONG` - Điểm trừ khi sai (mặc định: -2)
- `HINT_COST` - Giá gợi ý (mặc định: 10)
- `PASS_COST` - Giá bỏ lượt (mặc định: 20)

## 🗃️ Cấu Trúc Database

Bot sử dụng SQLite với 3 bảng chính:

- `game_states` - Lưu trạng thái game đang chơi
- `player_stats` - Thống kê người chơi
- `game_history` - Lịch sử các game đã chơi

## 🚀 Triển Khai 24/7

### Heroku

1. Tạo `Procfile`:

```
worker: python bot.py
```

2. Push lên Heroku và enable worker dyno

### Replit

1. Import project vào Replit
2. Thêm `DISCORD_TOKEN` vào Secrets
3. Run và enable Always On

### VPS

1. Sử dụng `screen` hoặc `tmux`
2. Hoặc tạo systemd service

## 🤝 Đóng Góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 TODO / Tính Năng Tương Lai

- [ ] API từ điển online (thay vì file txt)
- [ ] Chế độ thi đấu với thời gian giới hạn
- [ ] Achievements/badges
- [ ] Seasonal events
- [ ] Multi-guild leaderboard
- [ ] Voice channel integration
- [ ] Custom word packs

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết

## 💖 Credits

- Developed by Quoc Hung with ❤️ using discord.py
- Emoji từ Unicode Consortium
- Inspired by classic word chain games

## 🐛 Báo Lỗi

Nếu gặp lỗi, vui lòng tạo issue với:

- Mô tả lỗi chi tiết
- Steps để reproduce
- Screenshots nếu có
- Bot version và Python version

## 📞 Liên Hệ

- Facebook: https://facebook.com/hungnq188.2k5
- Email: hungnq.august.work@gmail.com

---

**Chúc bạn chơi vui vẻ!** 🎮✨
