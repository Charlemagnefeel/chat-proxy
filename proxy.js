const express = require("express");
const axios = require("axios");
const app = express();

app.use(express.json());

app.post("/chat", async (req, res) => {
  try {
    const userMessage = req.body.message || "Hi"; // 茉莉云传入的 message
    const response = await axios.post(
      "https://xiaoai.plus/v1/chat/completions",
      {
        model: "gpt-3.5-turbo",
        messages: [
          {
            role: "user",
            content: userMessage,
          },
        ],
      },
      {
        headers: {
          Authorization: "Bearer sk-wbdkdE8VNbd8d0TqEItWrHxGlWRyPZbyzrc6v71OwYvEUM2x",
          "Content-Type": "application/json",
        },
      }
    );
    res.json(response.data);
  } catch (err) {
    console.error("转发失败：", err.message);
    res.status(500).json({ error: "转发失败：" + err.message });
  }
});

app.listen(3000, () => {
  console.log("中转API运行在 http://localhost:3000/chat");
});
