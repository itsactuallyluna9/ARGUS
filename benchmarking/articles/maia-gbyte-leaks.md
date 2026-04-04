# Gbyte leaks gigabytes of data - #FuckStalkerware pt. 8

**plus an MMO boosting service, fully remote Android spying and patented ToS violations**

**content warnings:**

mentions of abuse/controlling behaviour

Almost two years ago now, in February 2024, a source reached out to me with data on a network of three stalkerware services: SpyX, MSafely and SpyPhone. They had found a publicly accessible reporting tool containing a comprehensive log of all purchases users of the services had made. Having been super busy with various other stories at the time, I put this aside for a few months until I started looking at the MSpy data leak.

Stalkerware operators often sign up to each others' services to scope out their competition or directly copy features, so it wasn't too surprising to find a SpyX email address in the MSpy helpdesk dump. Apparently, someone affiliated with SpyX had signed up to MSpy for two months, demanded a refund shortly after and then tried to charge back for the subscription, alleging credit card fraud. MSpy objected to the dispute and provided their payment processor with a detailed document outlining the SpyX affiliate's behavior. Contained within the document is redacted credit card details, including the name of the cardholder (Xunde Cheng) and their bank (China Construction Bank).

## Who runs SpyX?

The contact pages listed on websites operated by SpyX include Hong Kong and UK business registrations—Gbyte Technology Co., Limited and UK Gbyte Technology Co., Limited respectively—with the UK registration listing Xunde Cheng as an officer. A Google search for the Chinese company name listed in the Hong Kong registration (樂數科技有限公司) brings up the corporate website of Gbyte, as well as an entry on the BOSS Zhipin (BOSS直聘) hiring platform.

The BOSS listing and the corporate website both feature some photos of the Gbyte office in the Bao'an District of Shenzhen, with the hiring platform even containing a 360° panoramic image of its inside. Both pages also give us additional background on the company's history: It was founded in 2022 with a focus on "mobile forensics" software for an overseas market, and they ambitiously aim for an IPO within 5–10 years. The company also boasts about 50% of their staff being allocated to R&D, which they conduct together with universities.

A few months after first obtaining the bit of Gbyte data, I mentioned it to a person i was working on a tangentially related story with. Within just a few hours, they came back to me having looked into Gbyte themself, and they were able to gain broader access to Gbyte's stalkerware backends. In addition to the preexisting order data, we now also had copies of all user account data and victim metadata, including plaintext passwords for the stalkerware accounts and iCloud/Google credentials for a large number of victims. None of this data was meaningfully protected by any authentication; simply knowing which API endpoints were being called was enough to get the data. Additionally, another bug granted my source full access to the stalkerware's admin dashboard.

It was finally time for my favorite magic trick: You can often find the people who run spyware in their own spyware data. After a bit of combing through what I was given, I found what seemed to be email addresses belonging to Cheng. Up to this point, I wasn't sure whether that moniker was a pseudonym, but by running his emails through an OSINT research tool I was able to build a profile of the Gbyte founder.

Xunde Cheng (程勋德), aka Joen Chen, born February 1988, lives in Shenzhen and has a bachelor's degree in computer science from Beijing Jiaotong University. Before he started Gbyte, he was already an expert in mobile reverse engineering and forensics, having pioneered much of the technology the SpyX family of stalkerware is based on while working as chief security architect at Wondershare, the company behind utility software like Filmora as well as the Spyzie family of stalkerware.

## Spying from the Cloud

While at Wondershare, Cheng found ways to bypass the security measures of both iCloud and GMS, allowing forensics tools (including data recovery software, law enforcement tooling and stalkerware) access to cloud-synchronized device data with just a user's email and password. SpyX makes use of these capabilities to remotely spy on both iOS and Android devices.

While a lot of stalkerware software formerly offered this feature for iOS devices, most providers are now unable to keep up with Apple's cat-and-mouse-style API updates, so support has largely been dropped. But SpyX continues to be able to crack iCloud keystores, even on accounts with two-factor authentication. On Android, they are similarly able to crack GMS backups to spy on devices remotely, a capability no other stalkerware service I'm aware of offers, though SpyX does also provide a more traditional application-bound option.

Gbyte's trust in Google failing to enforce their various terms of service agreements is further exemplified by their stalkerware services allowing users to register via their Google accounts. This massively inflates their user counts, with roughly 60% of all users in the provided data being signed in this way. If Google were to revoke their access to the OAuth integration, SpyX would immediately—at least temporarily—lose a large part of their customer base.

Ironically, this Google integration (for once) makes it significantly harder for me to find any users of interest in the dataset, as most people are signed up with a personal Gmail rather than their work emails.

## What does Gbyte do?

From the photos and info on Gbyte's website, it appears that at least 20 people work for the company, and from BOSS it's known that they were actively hiring for a number of positions a few months ago. At this point, the only known products of theirs are three stalkerware offerings, a vague "mobile forensics" tool offered for the Chinese domestic market, and a foreign-market iOS data recovery tool.

From the data obtained so far, I was able to estimate that the SpyX family of stalkerware has netted Gbyte a total of around US$500,000 in revenue since launch. (To me, this does not appear to be enough to sustain a company of that size, especially when half its resources are allocated to R&D. It's probable that they have some other venture as well.)

It was right around when I calculated this number that my second source let me know that we had overlooked a key piece of evidence in the admin dashboard: a plaintext GitHub API key that had been available this whole time. The key provided access for what appears to be most of the source code for not just Gbyte's stalkerware and mobile forensics offerings, but also many other of their products, including:

- A GPS spoofing app with a paid subscription (ilocationchanger.com), having brought in approximately US$200 in revenue
- An MMO boosting service (igz.gg, fka igs.gg) with around 15,000 customers
- A now-defunct Elden Ring rune shop (eldenrings.com, aka eldenshop.com), which appears to use the same backend as igz.gg
- An AI copywriting and customer support tool (italks.cc), which seems to only be used internally for now
- The aforementioned three stalkerware services (spyx.com, msafely.com and spyphone.cc), which have around 1.5 million registered users in total
- The aforementioned Chinese device recovery and forensics tool (gbyte.com.cn)
- The aforementioned oversea-market device recovery tool (gbyte.com), with around 1,500 customers

Not included is the source code for the backends used to access the iCloud and Google Cloud services, the Android spyware client and some other smaller backend web services. They all appear to be hosted on a Synology NAS at the Gbyte office; based on a port scan, I assume the missing bits of source code are hosted on an SVN server on that NAS.

The backends we do have copies of, however, are all very similar to that of the stalkerware, meaning similar vulnerabilities are present. For most of the services mentioned above, data pertaining to orders, revenue, users and/or devices is accessible, often including email addresses, usernames, plaintext passwords, locations, real names and other sensitive information.

## Aftermath

Gbyte and Xunde Cheng were contacted about this story before it went live with information on all vulnerabilities found. They did not respond to the request for comment; no vulnerabilities have been patched prior to publication as a result.

Due to Have I Been Pwned misunderstanding an embargo I set in 2024, parts of the data this article is based on were already ingested into the services database in the first half of 2025 and some of the breach was covered in a TechCrunch article. A more complete and up-to-date dataset will be provided to Have I Been Pwned upon the publishing of this article and likely ingested as well. To prevent similar incidents from happening again, Have I Been Pwned will no longer receive advance copies of data going forward.

An earlier copy of the list of compromised iCloud accounts has been provided to Apple's Targeted Hacks team, and more up-to-date lists of affected Google and Apple accounts will be provided to the respective companies upon request.

The datasets of stalkerware customers/victims and MMO boosting customers will be provided to journalists and researchers upon request after vetting.
