# 📧 EMAIL SETUP GUIDE

## How to Enable Email Reports (Gmail)

---

## 🔐 **Step 1: Create Gmail App Password**

Since you're using Gmail, you need an "App Password" (not your regular password).

### **Instructions:**

1. **Go to Google Account Settings:**
   👉 https://myaccount.google.com/

2. **Navigate to Security:**
   - Click "Security" in the left sidebar

3. **Enable 2-Step Verification** (if not already):
   - Scroll to "2-Step Verification"
   - Follow the setup (required for App Passwords)

4. **Create App Password:**
   - Go back to Security
   - Scroll to "2-Step Verification"
   - At the bottom, click "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Name it: "DA-MCP"
   - Click "Generate"
   - **COPY the 16-character password** (looks like: xxxx xxxx xxxx xxxx)

---

## ⚙️ **Step 2: Configure Your MCP Server**

### **Option A: Environment Variables (Recommended)**

Update your Cursor MCP settings to include email config:

```json
{
  "mcpServers": {
    "da-mcp": {
      "command": "/Users/fei.zheng/Documents/Github/da-mcp/.venv/bin/python",
      "args": [
        "/Users/fei.zheng/Documents/Github/da-mcp/main.py"
      ],
      "env": {
        "DA_DATA_DIR": "/Users/fei.zheng/Documents/Github/da-mcp",
        "DA_EMAIL_SENDER": "your-email@gmail.com",
        "DA_EMAIL_PASSWORD": "xxxx xxxx xxxx xxxx",
        "DA_EMAIL_RECIPIENT": "your-email@gmail.com"
      }
    }
  }
}
```

**Replace:**
- `your-email@gmail.com` with your actual Gmail
- `xxxx xxxx xxxx xxxx` with the App Password you copied

---

### **Option B: Create .env File** (Alternative)

Create a file named `.env` in your project folder:

```bash
DA_EMAIL_SENDER=your-email@gmail.com
DA_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
DA_EMAIL_RECIPIENT=your-email@gmail.com
```

(Note: `.env` is already in `.gitignore` so it won't be committed to Git)

---

## ✅ **Step 3: Test It!**

After configuring email:

1. **Restart Cursor** completely

2. **Ask Cursor:**
   ```
   Generate my weekly sales report
   ```

3. **Check your email inbox!** 📬

---

## 🎯 **What You'll Get**

A beautiful HTML email with:
- 📊 Executive summary
- 📈 Table showing each region's performance vs benchmark
- 💡 Actionable recommendations
- ✅ Regions above target highlighted
- ⚠️ Regions below target flagged

---

## 🐛 **Troubleshooting**

### "Email not configured"
- ✅ Make sure you updated the Cursor MCP settings with your email
- ✅ Restart Cursor after changing settings

### "Authentication failed"
- ✅ Make sure 2-Step Verification is enabled on your Google account
- ✅ Double-check the App Password (no spaces when pasting)
- ✅ Use App Password, NOT your regular Gmail password

### "SMTP connection failed"
- ✅ Check your internet connection
- ✅ Some corporate networks block SMTP - try from home network

---

## 🔒 **Security Note**

Your App Password is stored in Cursor's settings. This is secure because:
- ✅ It's not your main Gmail password
- ✅ You can revoke it anytime from Google Account settings
- ✅ It's only visible to your local Cursor instance

**Never commit `.env` or settings with passwords to Git!**

---

## 💡 **Tips**

- You can send reports to different email addresses (change `DA_EMAIL_RECIPIENT`)
- Set up a weekly calendar reminder to run the report
- Later: We can automate this with cron/scheduled tasks

Enjoy your automated reports! 🎉
