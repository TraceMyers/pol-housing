# pol-housing

### A Zillow Data Scraper...
<p>... that was used to gather 8,000+ Zillow listings in two days. The data was collated with some IPUMS data and school distance data from the department of education, all of which is freely available <a href="https://drive.google.com/drive/folders/1Rl5qRtpXdoL3UPHq1YbVJX0fisJj8dwo?usp=sharing">here</a>.</p>
<p>It uses Selenium with a chrome web driver to browse Zillow like a real user. To that end, it selects from precalcuated random action timing distributions and uses mouse-overs to avoid CAPTCHA for as long as possible.</p>
<p>This script was single-use, as is the case with most scrapers. Zillow began to refuse connections from it by the end of the second day. However, it may be of some learning value.</p>
