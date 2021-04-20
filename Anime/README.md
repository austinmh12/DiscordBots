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
 This command replaces the message of the user who called it will ***SHEEeeee***eeesh, with a variable number of "e"'s between 4 and 1900. It can also mention another user. It displays the original sender at the very end of the message.

 **usage:** `.sheesh (es (4)) (user (None))`

#### sheesha
 This command replaces the message of the user who called it will ***SHEEeeee***eeesh, with a variable number of "e"'s between 4 and 1900. It can also mention another user. It doesn't say who sent the message to remain anonymous.

 **usage:** `.sheesh (es (4)) (user (None))`

### Waifus Cog
 This Cog provides the bot with a number of functions that parse the messages sent by MudaeBot to extract remaining times until a user can use a command again. It then periodically will send reminders mentioning users that have 5 minutes until they can use the command again. It has no commands itself, instead it just listens.

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

 **usage:** `.add_boofs <amount> (user (None))

#### remove_boofs
 This command is only runnable by me and removes boofs from the mentioned user as the listener sometimes adds multiple boofs if the MudaeBot hits the Discord message rate limit while the player keeps rolling.

 **usage:** `.remove_boofs <amount> (user (None))