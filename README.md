
# Job Application Aggregator

Job Application Aggregator is a Selenium-based system designed to automate and streamline the job application discovery process across multiple job platforms. It locates and evaluates job listings using highly customizable filters, presenting users with only the most relevant and actionable opportunities.

## 🧠 Key Concept

0. Install/Deploy
1. Configure your preferences and filters using `config.yml`.
2. Start the system and handle some foundation where needed (captchas, one-time codes).
3. Go get a coffee ☕—when you return, you’ll have dozens to hundreds of high-quality, curated job listings, some even pre-filled and ready to submit.

## 🔍 Supported Platforms

At the time of writing, Application Aggregator supports:

- [x] LinkedIn  
- [x] Indeed  
- [x] Glassdoor  

Support for additional platforms may have been added at the time of reading.

## ⚙️ Features

- 📝 **Application Pre-Fill**: Auto-fills “Easy Apply”–style job forms with saved applicant data. For external company websites, it opens the page and continues on.
- 🎯 **Advanced Filtering**: Apply highly granular filters to focus on jobs that match your specific criteria.
- 🧭 **Selenium-Powered Navigation**: Leverages browser automation to interact with pages as a user would.
- 🧪 **Human-in-the-Loop UX**: You can interact directly with the browser session to complete any dynamic fields or final submissions.

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- Google Chrome or Chromium
- ChromeDriver compatible with your browser version
- Docker (optional, for database deployment)

### Installation

```bash
git clone https://github.com/yourusername/application-aggregator.git
cd application-aggregator
./install.sh
docker-compose up -d	(If you don't have a database ready)
```

### Configuration

All major options—platform selection, filters, credentials, etc.—are managed through:

- `config.yml`: Your main settings file  
- `config_model.yml`: Schema to guide valid configuration

Make sure to read and customize these files before running.

### Running the Aggregator

```bash
./start.sh
```

The system will:
- Launch the selenium browser
- Log in (you may need to manually handle 2FA or captchas)
- Begin job discovery and collection


## ⚠️ Notes

- ❌ Email support is *not officially supported*. It exists solely to assist one-time-code logins for personal convenience.
- 🚧 While the system automates much of the workflow, **user supervision is required** during some interactions (e.g., captcha resolution, final application confirmations).

## 📜 License

[GPLv3](LICENSE)  
© 2025 Corey Merritt

