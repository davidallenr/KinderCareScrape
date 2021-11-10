### Prerequisites

This is an example of how to list things you need to use the software and how to install them.

- pip
- Python
- Chromedriver
- Selenium

### Installation

1. Get selenium chromedriver for your version of chrome [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)
2. Clone the repo
   ```sh
   git clone https://github.com/davidallenr/KinderCareImgScrape.git
   ```
3. Install Pip packages
   ```sh
   pip install selenium
   pip install python-decouple
   ```

````
4. Create .env file in root directory with these values
 ```sh
  WEBDRIVER_PATH = "path_to_chrome_driver"
  LOGIN_URL = "https://classroom.kindercare.com/login"
  DEBUG = False
  USERNAME = "your_login"
  PASSWORD = "your_password"
  WAIT_TIME = 5
  CHILDS_NAME = "your_kids_name"
````

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

This is mainly for my personal use but you're more than welcome to adapt it to your own needs.
This downloads all my kids images from the kindercare web app. It will check if the file exists before writing it.
Sleeps can be changed to whatever works for you.

<p align="right">(<a href="#top">back to top</a>)</p>
