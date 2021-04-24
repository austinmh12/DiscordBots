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

 Honestly of all the bots that I've made, this is probably my most impressive one and the one I'm most proud of. It seems like a small thing, but shoving the Minecraft server.jar into a process within the bot was no small task. The main reason being that once you'd start the server.jar file, the bot would no longer respond to commands, thus rendering all the commands useless.

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

 **usage:** `.tp <minecraft player name> <x coord or another minecraft player name> (y coord if x coord used) (z coord if x coord used)`

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

 I love this little game, and it's my most repository with the most commits. I think I went live in my discord server on version 0.0.7 when I implemented rolling, and now it's on version 3.1.3. This is still in active development but I've taken a small break to reorganise my bots into this folder and to come up with solutions to problems that the game currently faces.

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
 Shows the total boofs for the player or the player mentioned in the command. 

 **usage:** `.boofs (user (None))`

 _aliases: .b_

#### boofleaderboard
 Shows the leaderboard of player boofs and shows the player who ran the command's rank.

 **usage:** `.boofleaderboard`

 _aliases: .bl_

#### pokeroll
 Rolls the pokemon roulette for the player that called the command.

 **usage:** `.pokeroll`

 _aliases: .p_

#### pokecashrelease
 Releases a pokemon that the player owns for pokecash based on its rarity.

 **usage:** `.pokecashrelease <pokemon>`

 _aliases: .pr, .p_

#### pokecashautorelease
 Automatically releases any duplicate pokemon a player owns for pokecash of the passed rarity or lower.

 **usage:** `.pokecashautorelease (rarity (3))`

 _aliases: .parl, .arl_

#### pokedex
 Shows the player or mentioned player's pokedex, sortable by a number of methods, including id, name, duplicates, and more.

 **usage:** `.pokedex (user (None)) (sorting (id))`

 _aliases: .pd_

#### pokeserver
 Shows the leaderboards for the server (the whole bot actually, never stored guild_ids).

 **usage:** `.pokeserver (leaderboard (unique))`

 _aliases: .ps_

#### stats
 Shows the player or mentioned player's stats, including the number of times rolled, total pokecash earned, favourite pokemon, and various other stats tracked.

 **usage:** `.stats (user (None))`

 _aliases: .s_

#### timers
 Shows the time until you can do all the commands on timers.

 **usage:** `.timers`

 _aliases: .t_

#### pokemart
 Allows a player to view and purchase upgrades using pokecash gained from releasing pokemon.

 **usage:** `.pokemart (upgrade no (0)) (all (No))`

 _aliases: .pm, .mart_

#### pokerollall
 Rolled all the stored rolls a player has saved from battles.

 **usage:** `.pokerollall`

 _aliases: .pa_

#### trade
 Allowed a player to trade an owned pokemon with another player.

 **usage:** `.trade <user> <pokemon>`

 _aliases: .tr_

#### safarizone
 Allows a player to view and purchase pokemon that are randomly chosen daily.

 **usage:** `.safarizone (slot (0)) (amt (1))`

 _aliases: .sz_

#### daily
 A daily(ish) reward for players that rewarded extra rolls or cash.

 **usage:** `.daily`

 _aliases: .d_

#### pkmn
 Shows the information of the pokemon.

 **usage:** `.pkmn <pokemon>`

#### reminder
 Allows a player to receive a DM when the reminder they set goes off.

 **usage:** `.reminder (reminder (roll))`

 _aliases: .rd_

#### gift
 Allows a player to gift another player cash or rolls.

 **usage:** `.gift <user> <gift>`

 _aliases: .g_

#### badge
 Allows a player to trade in a certain number of pokemon for a badge of that pokemon. Later levels of badges award pokecash and extra rolls. If no pokemon is passed then all badges are shown.

 **usage:** `.badge (pokemon (None))`

##### badge all
 A subcommand of badge, automatically traded any eligible duplicate pokemon for badges.

 **usage:** `.badge all`

#### ditto
 Awarded a random duplicate pokemon to a player daily(ish).

 **usage:** `.ditto`

#### achievements
 Showed all the achievements with checkmarks next to the ones achieved.

 **usage:** `.achievements (user (None)) (category (all))`

 _aliases: .a, .ach_

#### pokehunt
 Allows a player to _hunt_ for a specific pokemon, increasing the chance that they would roll it.

 **usage:** `.pokehunt <pokemon>`

 _aliases: .ph, .hunt_

#### options
 Allows a user to turn off the confirmation message in the wondertrade command.

 **usage:** `.options <setting> <value>`

#### stars
 Shows the rarity of a pokemon without having to load the rest of the pokemon's information.

 **usage:** `.stars <pokemon>`

#### party
 Allows a player to add to or remove pokemon from their party, or view their party.

 **usage:** `.party (pokemon)/(pokemon)/...`

##### party clear
 A subcommand of party, clears and resets the player's party. Also fixes a bug when releasing a pokemon that was in the player's party.

 **usage:** `.party clear`

#### battle
 Battles a random trainer using the player's party, rewarding exp, pokecash, and extra rolls.

 **usage:** `.battle`

 _aliases: .bt_

#### daycare
 Allows a player to put a pokemon into the daycare, where it periodically rolls for bonus rewards based on its rarity.

 **usage:** `.daycare (pokemon (None))`

 _aliases: .dc_

##### daycare claim
 A subcommand of daycare, claims the current pokemon and rewards from the daycare. 

 **usage:** `.daycare claim`

#### savelist
 Allows a player to add pokemon to a list to prevent them from being auto released in the pokecashautorelease command.

 **usage:** `.savelist (pokemon)/(pokemon)/...`

 _aliases: .sl_

##### savelist clear
 A subcommand of savelist, clears the entire savelist.

 **usage:** `.savelist clear`

#### gym
 Allows a player to view or challenge a gym for a gym badge, exp, pokecash, and extra rolls. After obtaining all 8 badges, the player can challenge the elite four.

 **usage:** `.gym (slot (0))`

#### elitefour
 Challenges the elite four for exp, pokecash, and extra rolls. This can be done daily(ish)

 **usage:** `.elitefour`

 _aliases: .e4_

#### pokebox
 Shows the player or mentioned player's pokemon that have gained experience at least once.

 **usage:** `.pokebox (level (1))`

 _aliases: .pb_

#### wondertrade
 Allows a player to trade a random pokemon that they own for one of equal or better rarity.

 **usage:** `.wondertrade <pokemon>`

 _aliases: .wt_

#### saveparty
 Allows a player to save, load, or delete parties for quick switching between parties. Without using a subcommand, shows all the saved parties.

 **usage:** `.saveparty`

 _aliases: .sparty, .sp_

##### saveparty save
 Allows the player to save their current party for later loading.

 **usage:** `.saveparty save (slot (highest + 1))`

##### saveparty load
 Allows the player to load a saved party in place of their current one.

 **usage:** `.saveparty load <slot>`

##### saveparty delete
 Allows the player to delete a saved party.

 **usage:** `.saveparty delete <slot>`

#### raid
 Allows for multiple players to pit their parties against mega-evolved pokemon for a chance at obtaining them as a reward. This is the only way to receive mega-evolved pokemon outside of trading another player. This command shows how to start, join, or quit a raid, as well as the time remaining until the next raid.

 **usage:** `.raid (difficulty (None))`

##### raid join
 Allows a player to join a raid that has been initiated.

 **usage:** `.raid join`

##### raid quit
 Allows a player to quit a raid that hasn't been started.

 **usage:** `.raid quit`

##### raid start
 Allows the player who intiated the raid to start the raid.

 **usage:** `.raid start`

#### missing
 Shows all the pokemon that a player is missing.

 **usage:** `.missing`

 _aliases: .m_

#### favourite
 Sets a player's favourite pokemon which shows in the stats page.

 **usage:** `.favourite <pokemon>`

 _aliases: .favorite, .fav, .f_