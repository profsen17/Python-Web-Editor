# Python Web Code Editor: HTML, CSS, and JavaScript

Welcome to the **Python Web Code Editor**! This is a simple yet powerful Python application that helps you write, edit, and manage **HTML**, **CSS**, and **JavaScript** code with ease. Whether you're a beginner looking to learn the fundamentals of web development or an experienced developer needing a lightweight editor, this program provides the perfect environment to code for the web.

The goal of this project is to provide a **local desktop** solution for editing web code in an intuitive way, combining the power of Python with a user-friendly interface powered by **PyQt**.

## 📜 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 📝 Introduction

This project provides a GUI-based Python program that serves as a code editor specifically designed for web development. With this editor, you can write **HTML**, **CSS**, and **JavaScript** in an integrated, easy-to-use environment. The editor supports features that make coding more efficient and accessible, including syntax highlighting, live preview, and error detection.

You can think of this editor as a lightweight alternative to heavy IDEs, but specifically tailored to work with web technologies.

## 🚀 Features

- **HTML, CSS, JavaScript Editing**: Write clean and efficient web code with dedicated editors for HTML, CSS, and JavaScript.
- **Syntax Highlighting**: Each language has its own syntax highlighting to make code more readable and easier to debug.
- **Live Preview**: See the output of your HTML, CSS, and JavaScript code in real-time with an embedded web preview.
- **Error Detection**: Alerts you to common syntax errors in HTML, CSS, and JavaScript, making your development process smoother.
- **Code Auto-Completion**: Basic code completion suggestions for HTML tags, CSS properties, and JavaScript functions.
- **File Management**: Open, save, and organize your code files easily through an intuitive interface.
- **Cross-Platform**: The editor runs on Windows, macOS, and Linux.
- **Customizable Interface**: Change themes and layouts to match your coding style.
- **Lightweight**: A simple application that doesn't consume much system resource, perfect for web development on the go.

## 🖥️ Tech Stack

- **Python 3.x**: The primary language used for the program's backend logic.
- **PyQt5**: A powerful library that allows the creation of desktop applications with Python, used here to build the graphical user interface.
- **QWebEngineView**: Embedded web viewer used to show live previews of HTML files.
- **QSyntaxHighlighter**: Used to implement syntax highlighting for HTML, CSS, and JavaScript.
- **SQLite (optional)**: For storing custom user preferences or settings (optional).
- **Web Technologies (HTML/CSS/JS)**: The editor itself allows you to write these languages, making them the core content.

## 🛠️ Installation

To get started with this project, follow the steps below to install the editor and its dependencies.

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Step-by-Step Guide

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/python-web-code-editor.git
   cd python-web-code-editor

2. **Libraries to install**:
    ```bash
   pip install PyQt5
   pip install fuzzywuzzy
   pip install levenshtein
   pip install python-Levenshtein
   
