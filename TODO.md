# TODO

* [ ] histoire du oauth : comment faire valider l'application a usage personnel ?

* [X] Mettre en argument de la commande :
    * [X] le nom de la playlist youtube `arg[0]`
    * [X] le nom de la playlist spotify que l'on souhaite creer `arg[1]`
    * [X] (optionnel) description spotify playlist
* ~~Un autre script ? Update la playlist avec en arg en ligne de commande :~~
    --> tout dans le meme script
    * ~~le nom de la playlist spotify `arg[0]`~~
    * ~~le nom de la playlist youtube ou l'on doit aller recuperer les musiques `arg[1]`~~
* [X] Gerer les exceptions 
    * [X] si les playlists donnes en arguments n'existent pas
    * [X] si les videos de la playlist ne sont pas des musiques (est ce que spotify/yt gerent ca directement ?)
    * [X] titre en coreen 
    * [X] chansons en double (ne pas rajouter les chansons qui existent deja dans la spotify playlist)

## Organisation
* [X] classe Playlist(spotify_playlist_name, youtube_playlist_name) avec les methodes :
    * [X] create
    * [X] update
