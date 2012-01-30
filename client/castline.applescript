property app_id : "1234"
property app_secret : "5678"
# specific to the registered CastLine app

property interval : 5
property server : "castlineapp.appspot.com"
property redirect_url : "http://castlineapp.appspot.com/"
property fb_action_url : "https://graph.facebook.com/me/castline:listen_to"
global last_track
global oauth_win
global oauth_state
global oauth_code
global oauth_token

on run
	set last_track to missing value
	#	idle {}
	set oauth_state to 0 #unauthed
	tell application "Safari"
		activate
		if windows is {} then reopen
		set oauth_win to tab 1 of window 1
		set URL of oauth_win to "https://www.facebook.com/dialog/oauth?client_id=" & app_id & "&redirect_uri=" & redirect_url
		set oauth_state to 1 #waiting

	end tell
	idle {}
end run

on idle
	if oauth_state is 0 then #dead
		return 5
	end if
	if oauth_state is 1 then #authing
		tell application "Safari"
			try
				set redirect to URL of oauth_win as string
				set prefix to redirect_url & "?code="
				if redirect starts with prefix then
					set AppleScript's text item delimiters to {"=", "#"}
					set oauth_code to text item 2 of redirect
					close oauth_win

					set token_url to "https://graph.facebook.com/oauth/access_token" & Â
						"?client_id=" & app_id & Â
						"&redirect_uri=" & redirect_url & Â
						"&client_secret=" & app_secret & Â
						"&code=" & oauth_code

					set response to my httpget(token_url)
					set AppleScript's text item delimiters to {"=", "&"}
					set oauth_token to text item 2 of response
					set oauth_state to 2
				end if
			on error
				say "OAUTH FAILED"
				set oauth_state to 0
			end try
			return 0.1
		end tell
	end if
	#auth_state=2 authed
	#	try
	tell application "iTunes"
		if the player state is not playing then
			return interval
		end if
		set current_track to missing value
		if the podcast of the current track then
			set current_track to the current track
		end if
		if current_track is not missing value and current_track is not equal to last_track then

			set last_track to current_track
			set image to ""
			try
				set image to my encode(my b64(get raw data of artwork 1 of current track))
			end try
			set object_url to my httppost("http://" & server & "/action", Â
				"podcast_name=" & my encode(the album of the current track) & "&" & Â
				"podcast_episode_name=" & my encode(the name of the current track) & "&" & Â
				"podcast_episode_image=" & image Â
				)
			my httppost(fb_action_url, Â
				"access_token=" & oauth_token & "&" & Â
				"podcast_episode=" & my encode(object_url) Â
				)
			say "posted to open graph"
		end if
	end tell
	#	end try
	return interval
end idle

on encode(str)
	set encoder to "python -c \"" & Â
		"from sys import argv; " & Â
		"from urllib import quote; " & Â
		"print quote(unicode(argv[1], 'utf8'))" & Â
		"\" " & quoted form of (str)
	return do shell script encoder
end encode

on b64(bin)
	tell application "iTunes"
		set filename to (path to temporary items as string) & "castline.tmp"

		do shell script "touch " & POSIX path of filename
		set the handle to open for access file (filename) with write permission
		write bin to the handle
		close access handle
		set b64er to "python -c \"" & Â
			"from base64 import b64encode; " & Â
			"print b64encode(open('" & POSIX path of (filename) & "', 'r').read());\""
		set b64ed to do shell script b64er
		do shell script "rm " & POSIX path of filename
		return b64ed
	end tell
end b64

on httpget(uri)
	set getter to "curl " & quoted form of uri
	return do shell script getter
end httpget

on httppost(uri, body)
	set poster to "curl -d " & Â
		quoted form of body & " " & Â
		quoted form of uri
	return do shell script poster
end httppost
