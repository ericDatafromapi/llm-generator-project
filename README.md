# 🤖 LLM-Ready Generator

Transform any website into LLM-ready content with our easy-to-use generator. Create `llms.txt` files to make your website AI-discoverable!

## 🌟 Features

- **Lightning Fast**: Generate llms.txt files in seconds
- **Perfectly Formatted**: Clean, optimized content for LLMs
- **100% Free**: No signup, no limits
- **Multi-page Support**: Crawls your entire website
- **Real-time Progress**: Watch the generation happen live
- **Easy Download**: Get all files in one convenient ZIP

## 🚀 Live Demo

[Launch the Generator](#) <!-- Add your Streamlit Cloud URL here -->

## 📋 What is llms.txt?

`llms.txt` is the new standard for making websites easily readable by AI assistants like ChatGPT, Claude, and Perplexity. When users ask AI about your business, having an llms.txt file ensures your content is accurately represented.

Learn more at [llmstxt.org](https://llmstxt.org)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Crawler**: Mdream (via npx)
- **Backend**: Python 3.x

## 📦 Installation

### Prerequisites

- Python 3.8+
- Node.js and npm (for npx)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-ready-generator.git
cd llm-ready-generator
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
streamlit run app.py
```

5. Open your browser to `http://localhost:8501`

## 🎯 Usage

1. **Landing Page**: Learn about llms.txt and its benefits
2. **Launch Generator**: Click the CTA button to access the generator
3. **Enter URL**: Input the website you want to process
4. **Configure** (Optional): Adjust max pages, patterns, etc.
5. **Generate**: Click "Start Generation" and wait
6. **Download**: Get your llms.txt and supporting files

## 📁 Generated Files

The generator creates:
- `llms.txt` - Concise summary for LLMs
- `llms-full.txt` - Complete content with metadata
- `manifest.json` - Generation metadata
- `*.md` - Individual markdown files for each page

## 🔄 Deployment to Streamlit Cloud

### Required Files for Deployment

Make sure these files are in your repository:
- `app.py` - Main application
- `llmready_min.py` - Crawler script
- `requirements.txt` - Python dependencies
- `packages.txt` - System packages (Node.js and npm)

### Deployment Steps

1. Push your code to GitHub (including `packages.txt`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with one click!

Streamlit Cloud will automatically:
- Install Python dependencies from `requirements.txt`
- Install system packages from `packages.txt` (Node.js and npm)
- Run your app

### Environment Variables

No environment variables required for basic deployment.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

- Powered by [Mdream](https://github.com/harlan-zw/mdream)
- Inspired by the [llms.txt](https://llmstxt.org) initiative
- Built with [Streamlit](https://streamlit.io)

## 📧 Support

Have questions or issues? [Open an issue](https://github.com/yourusername/llm-ready-generator/issues) on GitHub.

---

Made with ❤️ for the AI-first web