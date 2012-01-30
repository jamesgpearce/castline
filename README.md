# CastLine

## Posting your podcast habits to the Open Graph

Uses AppleScript to detect what podcast you are listening to.

Posts the objects (for episode and podcast series) to a Google App Engine instance.

Posts the listening action to the open graph, so you can log your listening habits and share with friends.

(It also talks to you to tell you it posted an action.)

With this, I see my listening turning up in Timeline thus:

![](http://cl.ly/Djul/2Dl4.png)

### This code won't work

Firstly because I removed the app_id and app_secret required, but also because the castline actions are not approved and so only named developers and testers can submit actions to appear in their ticker and timeline.

Nevertheless, if you ever wondered how you might hack OAuth2 with AppleScript, or b64 encoding artwork by shelling out to python, this might be interesting.

Also the GAE piece might demonstrate an interesting start to a generic OG-centric model & handler framework.

On the whole, this is a small personal project, and certainly not intended as readable, re-usable industrial-grade code :-)
