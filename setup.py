"""
Setup script - Tự động cài đặt và cấu hình bot
"""
import os
import sys
import subprocess

def print_header(text):
    """In header đẹp"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python_version():
    """Kiểm tra Python version"""
    print_header("🐍 Kiểm Tra Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8+ is required!")
        print("Please upgrade Python and try again.")
        return False
    
    print("✅ Python version OK!")
    return True

def install_dependencies():
    """Cài đặt dependencies"""
    print_header("📦 Cài Đặt Dependencies")
    
    try:
        print("Installing packages from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        return False

def create_directories():
    """Tạo các thư mục cần thiết"""
    print_header("📁 Tạo Thư Mục")
    
    dirs = ['data', 'logs']
    
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ Created directory: {dir_name}")
        else:
            print(f"ℹ️  Directory already exists: {dir_name}")
    
    return True

def setup_env_file():
    """Tạo .env file từ template"""
    print_header("⚙️ Cấu Hình Environment Variables")
    
    if os.path.exists('.env'):
        print("ℹ️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Skipping .env creation")
            return True
    
    # Copy from .env.example
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        print("\n" + "-"*60)
        print("Please enter your Discord Bot Token")
        print("(Get it from: https://discord.com/developers/applications)")
        print("-"*60)
        
        token = input("Discord Bot Token: ").strip()
        
        if not token:
            print("⚠️  Warning: No token provided!")
            print("You'll need to manually edit .env file later")
        
        # Replace token in content
        content = content.replace('DISCORD_TOKEN=your_bot_token_here', f'DISCORD_TOKEN={token}')
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ .env file created successfully!")
        
        if not token:
            print("\n⚠️  Remember to add your Discord token to .env before running the bot!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_word_lists():
    """Kiểm tra danh sách từ"""
    print_header("📚 Kiểm Tra Danh Sách Từ")
    
    files = {
        'data/words_vi.txt': 'Vietnamese',
        'data/words_en.txt': 'English'
    }
    
    for file_path, lang in files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                word_count = len([line for line in f if line.strip()])
            print(f"✅ {lang} words: {word_count} words loaded")
            
            if word_count < 100:
                print(f"   ⚠️  Warning: Only {word_count} words. Consider adding more!")
        else:
            print(f"❌ Missing: {file_path}")
    
    return True

def print_next_steps():
    """In hướng dẫn tiếp theo"""
    print_header("🚀 Setup Complete!")
    
    print("Next steps:")
    print()
    print("1. Make sure your Discord Bot Token is in .env file")
    print("2. Invite bot to your server with these permissions:")
    print("   - Send Messages")
    print("   - Embed Links")
    print("   - Read Message History")
    print("   - Use Slash Commands")
    print()
    print("3. Run the bot:")
    print("   python bot.py")
    print()
    print("4. In Discord, use /help to see all commands")
    print()
    print("Optional: Add more words to data/words_vi.txt and data/words_en.txt")
    print()
    print("="*60)
    print("  🎮 Happy Gaming! ✨")
    print("="*60)

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("  🎮 Discord Word Chain Bot - Setup Wizard")
    print("="*60)
    
    # Run checks
    if not check_python_version():
        return
    
    if not install_dependencies():
        return
    
    create_directories()
    setup_env_file()
    check_word_lists()
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
