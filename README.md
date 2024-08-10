
---

# 项目名称

欢迎来到我的项目！🎉

## 项目简介

本项目是对以下两个教程的本地部署版本，旨在简化最后一步的邮箱发送功能：

- [Bilibili 教程](https://www.bilibili.com/video/BV1H4421X7Wg)
- [YouTube 教程](https://www.youtube.com/watch?v=smWrAZq_2Fg)

通过本项目，您可以方便地在本地环境中进行邮箱发送操作，提升您的工作效率！🚀

## 使用说明

1. **克隆项目**  
   首先，您需要将本项目克隆到本地：
   ```bash
   git clone https://github.com/ls2023wsw/-cf-resend-.git
   cd -cf-resend-
   ```

2. **配置 API Key**  
   在 `app.py` 文件中，找到以下部分并输入您的 Resend API Key：
   ```python
   resend.api_key = '你的apikey'
   ```

3. **修改后台管理账号和密码**  
   同样在 `app.py` 中，您可以找到后台管理的账号和密码设置，请自行修改：
   ```python
   ADMIN_USERNAME = ""
   ADMIN_PASSWORD = ""
   ```
   以及App.py里面的第208行，邮箱后缀改成你的域名设置的那个

4. **部署项目**  
   完成配置后，您可以根据您的环境进行部署，例如使用 Flask 运行：
   ```bash
   python app.py
   ```

## 反馈与支持

如果您在使用过程中遇到任何问题，欢迎随时联系我！😊



希望这个版本能够满足你的需求！如果需要进一步修改或添加内容，请告诉我。
