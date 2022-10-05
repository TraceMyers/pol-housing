# pol-housing

### A Zillow Data Scraper...
<p>... that was used to gather 8,000+ Zillow listings in two days. The data was collated with some IPUMS data and school distance data from the department of education, all of which is freely available <a href="https://drive.google.com/drive/folders/1Rl5qRtpXdoL3UPHq1YbVJX0fisJj8dwo?usp=sharing">here</a>.</p>
<p>It uses Selenium with a chrome web driver to browse Zillow like a real user. To that end, it selects from precalcuated random action-timing distributions and uses superfluous mouse-overs to avoid CAPTCHA for as long as possible. It also uses multiprocessing to allow for multiple Selenium instances at once. Having spent more time with asynchronous programming now, I see that multithreading would have been a better choice.</p>
<p>This script likely no longer works, and it was not written to be extended or malleable. However, it may be of some learning value.</p>
