# DnDxMTG
 This bot serves the purpose of creating MTG decks, showing cards, and then _playing_ MTG. Its development is soley for me and my buddy's homebrew DnD crossed with MTG campaign that we've been developing.

## Card
 This is what allows for the searching and displaying of cards in discord.

 **Command List**
 * searchcards
 * searchcard

#### searchcards
 Allows a user to search for multiple cards, showing a paginated result sorted alphabetically.

 **usage:** `.searchcards <search term>`

 _aliases: .sc_

#### searchcard
 Allows a user to search for a single card.

 **usage:** `.searchcard <search term>`

 _aliases: .s_

## Deck
 This allows for player to see, create, and modify decks.

 **Command List**
 * create_deck
 * search_decks
 * list_decks

#### create_deck
 This allows player to create an empty deck with a name.

 **usage:** `.create_deck <name>`

 _aliases: .cd_

#### search_decks
 This allows player to search for a deck they created.

 **usage:** `.search_decks <name>`

 _aliases: .sd_

#### list_decks
 This allows player to list all the decks they've created.

 **usage:** `.list_decks`

 _aliases: .ld_

## Game
 This cog only translates MTG keywords into their DnD counterparts.

 **Command List**
 * keyword

#### keyword
 Gave the DnD definition of the MTG keyword.

 **usage:** `.keyword <keyword>`

 _aliases: .kw_

## GM
 This is the cog that allowed for the GM to manage the BTS things such as registering players to channels, deleting decks, etc.

 **Command List**
 * registerchannel
 * delete_deck

#### registerchannel
 Registers a user to a discord channel, preventing others from using commands in it.

 **usage:** `.registerchannel <user>`

 _aliases: .rc_

#### delete_deck
 Deletes a deck that a user has

 **usage:** `.delete_deck <user> <name>`

 _aliases: .dd_