# Anime
 The Anime bot folder contains two bots, ecchi_pics and mudae. ecchi_pics is a reddit scraping image bot and mudae is a lot of things under one roof.

## ecchi_pics
 This bot scrapes a list of subreddits that can be added by users in the server. It has a couple commands to fetch already downloaded images. Once per day it would go through the last 50 posts in hot per subreddit registered, then download any images from those posts. It would use the post's NSFW flag to determine whether the image was NSFW or not, then upload to the designated channels in the server for them. 

 _**This was never updated to the .env structure and is very outdated.**_

 **Command List**
 * animepic
 * ecchipic
 * subreddit

#### animepic
 This command allows a user to have the bot upload a number of SFW images to a channel.

 **usage:** `.animepic (number (1))`

 _aliases: .ap, .pic_

#### ecchipic
 This command allows a user to have the bot upload a number of NSFW images to a channel.

 **usage:** `.ecchipic (number (1))`

 _aliases: .ep, .echpic_

#### subreddit
 This command allows a user to add a subreddit to the list of subreddit to search. If not subreddit is passed, then it shows the list of registered subreddits.

 **usage:** `.subreddit (subreddit name (''))`

 _aliases: .sub, .subs, .sr_

## mudae
 This bot originally started as a bot to accompany MudaeBot, hence the name, but evolved to do a lot more. On top of giving notifications when various timers were up to users from the MudaeBot games, it can also run a minecraft server, and has it's own PokeRoulette game.
 
 **Command List** _Note: This list does not include the cogs, those are in each cog section._
 * sheesh
 * sheesha

#### sheesh
 This command replaces the message of the user who called it with ***SHEEeeee***eeesh, with a variable number of "***e***"'s between 4 and 1900. It can also mention another user. It displays the original sender at the very end of the message.

 **usage:** `.sheesh (es (4)) (user (None))`

#### sheesha
 This command replaces the message of the user who called it with ***SHEEeeee***eeesh, with a variable number of "***e***"'s between 4 and 1900. It can also mention another user. It doesn't say who sent the message to remain anonymous.

 **usage:** `.sheesha (es (4)) (user (None))`

### Waifus Cog
 This cog provides the bot with a number of functions that parse the messages sent by MudaeBot to extract remaining times until a user can use a command again. It then periodically will send reminders mentioning users that have 5 minutes until they can use the command again. It has no commands itself, instead it just listens.

### Pokemons Cog
 Much like the Waifus cog, this does the same, but listens for the pokemon minigame from the MudaeBot. In addition, it also has commands to show a player's _bOofs_, which is when a player rolled 0 pokemon in the pokeslots.

 **Command List**
 * mudaeboofs
 * mudaeboofleaderboard
 * add_boofs
 * remove_boofs

#### mudaeboofs
 This command displays the user who called it, or the mentioned user's boofs from the MudaeBot.

 **usage:** `.mudaeboofs (user (None))`

 _aliases: .mb, .boof, .bOof, .bOofs_

#### mudaeboofleaderboard
 This command displays a list of the users who it's captured playing the MudaeBot Pokeslot game and displays the number of bOofs they have. At the bottom it displays the user who called the command's rank among the list.

 **usage:** `.mudaeboofleaderboard`

 _aliases: .mbl, .pblb, .bOofleaderboard, .bOoflb, .bOofl_

#### add_boofs
 This command is only runnable by me and adds boofs to the mentioned user as the listener sometimes misses messages if they go to fast.

 **usage:** `.add_boofs <amount> (user (None))`

#### remove_boofs
 This command is only runnable by me and removes boofs from the mentioned user as the listener sometimes adds multiple boofs if the MudaeBot hits the Discord message rate limit while the player keeps rolling.

 **usage:** `.remove_boofs <amount> (user (None))`

### Minecraft Cog
 This cog allowed anyone in the server to add and remove mods and start and stop the minecraft server as I had the spare resources on my PC to run it and the best internet of the group, but wasn't always available to add things for them. Later I added the ability for people in the server to run certain commands as if they were ops, but without opping them in the server (for no reason other than why not?)

 **Command List**
 * add_mod
 * remove_mod
 * list_mods
 * start
 * stop
 * restart
 * status
 * tp
 * list
 * weather
 * clear
 * rain
 * thunder
 * time
 * day
 * night
 * midnight
 * noon
 * say

#### add_mod
 This command allowed a user to upload a mod to the mods folder of the server (in hindsight this is a terrible idea).

 **usage:** `.add_mod` when uploading a .jar file

 _aliases: .am_

#### remove_mod
 This command allowed a user to delete a mod from the server (also a terrible idea, since there's no voting or confirmation).

 **usage:** `.remove_mod <mod name>`

 _aliases: .rm_

#### list_mods
 This command lists the mods that the server currently has.

 **usage:** `.list_mods`

 _aliases: .lm_

#### start
 Starts the minecraft server.

 **usage:** `.start`

#### stop
 Stops the minecraft server.

 **usage:** `.stop`

#### restart
 Restarts the server by calling stop and then start.

 **usage:** `.restart`

#### status
 Returns the status of the server, whether it's online or offline.

 **usage:** `.status`

#### tp
 Passes the tp command to the minecraft server.

 **usage:** `.tp <minecraft player name> <x coord or another minecraft player name> (y coord) (z coord)`

#### list
 Lists the players that are currently online in the minecraft server.

 **usage:** `.list`

 _aliases: .online_

#### weather
 Passes the weather command to the minecraft server.

 **usage:** `.weather <type> (duration (120))`

#### clear
 A shortcut to using .weather clear

 **usage:** `.clear (duration (120))`

#### rain
 A shortcut to using .weather rain

 **usage:** `.rain (duration (120))`

#### thunder
 A shortvut to using .weather thunder

 **usage:** `.thunder (duration (120))`

#### time
 Passes the time command to the minecraft server

 **usage:** `.time <set or add> <amt>`

#### day
 A shortcut to using .time set day

 **usage:** `.day`

#### night
 A shortcut to using .time set night

 **usage:** `.night`

#### midnight
 A shortcut to using .time set midnight

 **usage:** `.midnight`

#### noon
 A shortcut to using .time set noon

 **usage:** `.noon`

#### say
 Allows for discord messages to be sent to the minecraft server using the minecraft say command and appears in minecraft as `discord nickname: message`

 **usage:** `.say <message>`

### PokeRoulette Cog
 This cog is my own Pokemon Roulette game. Players roll for pokemon of varying rarities, release them for pokecash, then use that cash to buy upgrades. It also allowed users to create parties, battle trainers, gyms, and the elite four, and participate in raids to earn mega-evolved pokemon.

 **Command List**
 * boofs
 * boofleaderboard
 * pokeroll
 * pokecashrelease
 * pokecashautorelease
 * pokedex
 * pokeserver
 * stats
 * timers
 * pokemart
 * pokerollall
 * trade
 * safarizone
 * daily
 * pkmn
 * reminder
 * gift
 * badge
 * badge all
 * ditto
 * achievements
 * pokehunt
 * options
 * stars
 * party
 * party clear
 * battle
 * daycare
 * daycare claim
 * savelist
 * savelist clear
 * gym
 * elitefour
 * pokebox
 * wondertrade
 * saveparty
 * saveparty save
 * saveparty load
 * saveparty delete
 * raid
 * raid join
 * raid quit
 * raid start
 * missing
 * favourite

#### boofs


 **usage:** ``

 _aliases: _

#### boofleaderboard


 **usage:** ``

 _aliases: _

#### pokeroll


 **usage:** ``

 _aliases: _

#### pokecashrelease


 **usage:** ``

 _aliases: _

#### pokecashautorelease


 **usage:** ``

 _aliases: _

#### pokedex


 **usage:** ``

 _aliases: _

#### pokeserver


 **usage:** ``

 _aliases: _

#### stats


 **usage:** ``

 _aliases: _

#### timers


 **usage:** ``

 _aliases: _

#### pokemart


 **usage:** ``

 _aliases: _

#### pokerollall


 **usage:** ``

 _aliases: _

#### trade


 **usage:** ``

 _aliases: _

#### safarizone


 **usage:** ``

 _aliases: _

#### daily


 **usage:** ``

 _aliases: _

#### pkmn


 **usage:** ``

 _aliases: _

#### reminder


 **usage:** ``

 _aliases: _

#### gift


 **usage:** ``

 _aliases: _

#### badge


 **usage:** ``

 _aliases: _

#### badge all


 **usage:** ``

 _aliases: _

#### ditto


 **usage:** ``

 _aliases: _

#### achievements


 **usage:** ``

 _aliases: _

#### pokehunt


 **usage:** ``

 _aliases: _

#### options


 **usage:** ``

 _aliases: _

#### stars


 **usage:** ``

 _aliases: _

#### party


 **usage:** ``

 _aliases: _

#### party clear


 **usage:** ``

 _aliases: _

#### battle


 **usage:** ``

 _aliases: _

#### daycare


 **usage:** ``

 _aliases: _

#### daycare claim


 **usage:** ``

 _aliases: _

#### savelist


 **usage:** ``

 _aliases: _

#### savelist clear


 **usage:** ``

 _aliases: _

#### gym


 **usage:** ``

 _aliases: _

#### elitefour


 **usage:** ``

 _aliases: _

#### pokebox


 **usage:** ``

 _aliases: _

#### wondertrade


 **usage:** ``

 _aliases: _

#### saveparty


 **usage:** ``

 _aliases: _

#### saveparty save


 **usage:** ``

 _aliases: _

#### saveparty load


 **usage:** ``

 _aliases: _

#### saveparty delete


 **usage:** ``

 _aliases: _

#### raid


 **usage:** ``

 _aliases: _

#### raid join


 **usage:** ``

 _aliases: _

#### raid quit


 **usage:** ``

 _aliases: _

#### raid start


 **usage:** ``

 _aliases: _

#### missing


 **usage:** ``

 _aliases: _

#### favourite


 **usage:** ``

 _aliases: _
