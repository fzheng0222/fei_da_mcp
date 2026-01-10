# 🎯 CURSOR MCP CONFIGURATION

## Copy & Paste This Into Your Cursor Settings!

---

## 📋 **Step 1: Open Cursor MCP Settings**

1. In Cursor, press **`Cmd + ,`** (Mac) or **`Ctrl + ,`** (Windows/Linux)
2. In the search bar, type: **`mcp`**
3. Click on **"MCP Servers"** or look for **"Edit in settings.json"**
4. This opens your MCP configuration file

---

## 📝 **Step 2: Paste This Configuration**

Copy and paste this ENTIRE block into your Cursor MCP settings:

```json
{
  "mcpServers": {
    "da-mcp": {
      "command": "/Users/fei.zheng/Documents/Github/da-mcp/.venv/bin/python",
      "args": [
        "/Users/fei.zheng/Documents/Github/da-mcp/main.py"
      ],
      "env": {
        "DA_DATA_DIR": "/Users/fei.zheng/Documents/Github/da-mcp"
      }
    }
  }
}
```

---

## 🔍 **What This Means:**

- **`da-mcp`** - The name of your MCP server (you can change this)
- **`command`** - Path to Python in your virtual environment
- **`args`** - Path to your main.py file
- **`env.DA_DATA_DIR`** - Where your CSV files are located

---

## 🔄 **Step 3: Restart Cursor**

**IMPORTANT:** You MUST completely restart Cursor!

- **Mac:** Press `Cmd + Q`, then reopen Cursor
- **Windows/Linux:** Close Cursor completely, then reopen

---

## ✅ **Step 4: Verify It Works**

After restarting, try these in Cursor's chat:

1. **"What tables are available?"**
   - Should show "sales_data" table

2. **"Show me the schema of sales_data"**
   - Should show columns: date, region, sales, benchmark, etc.

3. **"Query the sales_data table"**
   - Should return the actual data!

---

## 🎉 **You're Done!**

If you see your data, congratulations! Your DA-MCP server is working! 🚀

---

## 🐛 **Troubleshooting**

### Problem: "MCP server not found"
- ✅ Check the file paths are correct
- ✅ Make sure you completely restarted Cursor
- ✅ Check `.venv` folder exists

### Problem: "Command failed"
- ✅ Run this to test: `.venv/bin/python main.py`
- ✅ Check for errors in terminal

### Problem: "No tables found"
- ✅ Make sure `sales_data.csv` exists in the folder
- ✅ Check the DA_DATA_DIR path is correct

---

## 💡 **Next Steps**

Once it's working, try these queries:

- "Show me sales by region"
- "Which regions exceed their benchmark?"
- "Compare sales to benchmark for each region"
- "What's the average sales by region?"

Have fun! 🎊
