# super-ds9

A modernization of the 1971 Star Trek terminal based text game. Written in Python and set during a number of scenerios.

1. Diffrences between Super DS9 and both the 1971 Star Trek and 1978 Super Star Trek games:

    While Super DS9 is heavly inspired by Super Star Trek, ther are a number of diffrences.

    A. Set in Stone Diffrences:

        i. Energy:

            Running out of energy is no longer the death sentacne that it used to be. Now, your will regerate a small amout of energy each turn. When 
            out of combat, using the Repair command will allow much greater energy restoration. No need to go mining dilithium crystals!

        ii. In-System Movement:

            When moving within a system, impulse power is always used. Moving via impulse always takes one turn. Warp travel is reserved to traveling 
            from one system to another. Furthermore, moving via warp with shields up takes no extra energy.
        
        iii. Energy Weapons:

            Phasers, disruptors, and other energy weapons can safly be fired with the shields up, so starship captains don't need to fool around with 
            energy-hungry option of rapid lower-fire-raiseing their shields, firing, and then raising them.

        iv. Torpedos:

            No longer is the player limited to photon torpedos, now the more powerful quantium torpedos are avaliable as well! On the down side, 
            torpedos are no longer one hit kills against most enemies.

        v. Equilivancy:

            In general, you should assume that everything your ship can do, your enemy can also do.

        vi. No Backup Ship:

            There's no option to abandon your current ship and switch ot another one.

    B. Diffrences for Now:

        i. Nova and Supernova:

            So far, stars will not erupt in a nova when hit by torpedos. This will probably change. It remains to be seen how many torpedos it will take 
            to induce a nova, however...

        ii. Communications:

            Future versions will probably include a communications system to call for renforcements.

    C. Former Diffrences:

        i. Cloaking Device:

            Ships can cloak now! Just be sure that your enemies sensors can't detect you.
        
        ii. One Difficulty Level:

            Three levels of difficulty are currently avaliable.
        
        iii. Starbases:

            Ships are able to dock with friendly starbases. In addition to crewed starbases, there are also automated non-dockable defense platforms.
        
        iv: Instant Warp Travel:

            Warping is not instant, and selecting a higher warp speed will allow for faster travel, however this will consume more energy.
        
        v. Life Support:

            If life support goes offline for several turns, crew will begin to die.

        iii. Starbases:

            Ships are able to dock with friendly starbases. In addition to crewed starbases, there are also automated non-dockable defense platforms.
        
        iv: Instant Warp Travel:

            Warping is not instant, and selecting a higher warp speed will allow for faster travel, however this will consume more energy.
        
        v. Life Support:

            If life support goes offline for several turns, crew will begin to die.

        vi. Long Range Scans:

            In order to determin if a system contains hostile ships or stations, you must be in range of your ship's scanner.

2. User Interface Basics

    User interface elements are rectangles drawn on the screen with titles and/or text contained in their bodies. They respond to the user clicking on 
    them, keyboard input, or both. There are several types of user interface elements used in this game:

    A. Button:

        This is the most basic input element. Clicking on it, or pressing the key that triggers it will call the effect associated with the button.

    B. Toggleable:

        Click on them to toggle them between their two states, on and off. Often, they can also be toggled by pressing a key indicated in their title.

        Their color will change to indicate their current state, as will the text in the body of the toggleable element.

    C. Text Input:

        A text input element responds to keystrokes. Characters can be entered or deleted at the position of the cursor.

        Often, the text element must be slected first by clicking on it before text can be input.

    D. Numerical Input:

        These differ from a text element in that they will only accept numerical input. They also have a minimum and maximum value, if the user attempts 
        to enter a number that is higher then the maximum value then it will be capped at the maximum. 
        
        Another difference is that sometimes the user can increment the stored number using the up and down keys. How much it is incremented is 
        determined by the position of the cursor. If the tens place is highlighted by the cursor, then the number will be incremented by plus or minus 
        ten.
        
        Some numerical elements will allow for a number to 'loop' if it exceeds the minimum or maximum allowed values. When these elements are 
        incremented, if the new value is over the limit, then it will loop to be under the limit and vice versa.

        For example, say an element has a minimum value of 100, and a maximum value of 50000. The current value is 120. The user decrements the tens 
        value three times. This leaves the value at 90. However, as that is ten less the minimum value, the value loops around to 49990.

    E. Menu Input:

        A menu element offers a selection of items. Clicking on one of the items will select it.

3. Starting a new game:

    Here, the player has the option to change the default names of their ship and captain, as well as randomly choosing a ship name.

    A. Options:

        Easy Aim - Allows the user the enter torpedo coordinates, instead of entering a heading.

        Easy Warping - Allows the user the enter the coordinates of the system they want to warp to, instead of entering a heading and distance.

        Easy Movement - Allows the user the enter the coordinates of the location they want to warp to, instead of entering a heading and distance.

        3-D movement - When on, ships will only collide with stars/planets/ships if their destination position is the same as the star/planet/ship they 
        are colliding with. When off, a ship will collide will any object between it and it's destination.

        Torpedo Warnings - The system will warn the player if the coordinates/heading they have entered will result in the torpedo missing, or if it 
        risks hitting a star, planet, or friendly ship. The player is free to ignore this warning.

        Crash Warnings - The system will warn the player if the coordinates/heading and distance they have entered risks their ship hitting a star, 
        planet, or ship. The player is free to ignore this warning.

        Random Name - This button will randomly select a name from the player's nation.

    B. Other Options:

        Captain Name - This allows the player to change the name of the ship captain from the default name.

        Ship Name - This allows the player to change the name of the ship from the default name.

        Begin - Starts the game.

        Cancel - Returns to the main screen.

4. Game Interface:

    The game screen is divided into several sub-screens:

    A. Sector: 
    
        This shows all the star systems in the sector displayed in a grid arrangement. The system that the player is located in is highlighted in white.

        Each system has several values:

            Number of stars in the system - yellow number to the right of astrix (*) symbol, located in top right

            Number of barren planets in the system - dark grey number to the right of plus symbol, located in top left

            Number of hostile/undeveloped planets in the system - magenta number to the right of plus symbol, located in middle left

            Number of allied planets in the system - green number to the right of plus symbol, located in lower left

            Number of small enemy ships in the system - red number to the right of plus symbol, located in middle right

            Number of large enemy ships in the system - red number to the right of plus symbol, located in lower right

    B. Message Log: 
    
        This displays messages that the player has received over the course of the game.

    C. System: 
    
        This shows the stars, planets, and ships that are located in the same system as the player.

        Stars are displayed as astrix (*) symbols, planets as pound (#) symbols, and ships as upper case letters.

        The player is highlighted by a white box, and their selected ship/planet/star is highlighted by an orange box.
        
        i. Planet Types:

            Uninhabited - These planets do not possess sentient life. They are indicated with an orange color.

            Pre-Warp - These are too primitive to be of any assistance to you (or anyone else). They are displayed with a grey color.

            Friendly - Friendly planets have warp capabilities and are willing to help repair and resupply the player. They are indicated with a lime 
            color.

            Hostile - These planets have warp drive, but are not willing to assist the player. They are indicated with a purple color.

            Angered - If the player hits a friendly planet with a torpedo, it will become angered, and will no longer help supply and repair the player. 
            They are indicated with a purple color.

            Formerly Inhabited - if a planet is hit with enought torpedoes to destroy it's civilisation, it will become Formerly Inhabited. They are 
            displayed with a grey color.

        ii. Ships:

            Ships are normaly the same color as their nation, that is to say that Federation ships are blue, Klingon ships are red, Dominion ships are 
            purple, Romulan ships are green, and so forth. 

            However, a ship will be displayed in a white color if it is derelict, or a grey color if it has been reduced to a hulk.
            
    D. Status: 
    
        The sub screen shows the player's alert status. Condition Red is shown if there are enemy ships present, Condition Blue if the player is docked 
        at a planet, and Condition Yellow otherwise

        Local pos - This is the player's X and Y location in the system.

        System pos - This is the X and Y location of the system that they are located in.

        Stardate - This is the current stardate.

        Ending stardate - If the current stardate reaches this, the scenerio will end.

    E. Command: 
    
        This will show buttons for different ship commands, such as going to warp, firing energy weapon arrays, ect.

    F. Player Ship Information: 
    
        This desplays information about the players ship.

        i. Basic Information:

            Shields/Maximum Shields - This shows the player's current and maximum shields.

            Hull/Maximum Hull - Current and maximum hull strength.

            Energy/Maximum Energy - Current and maximum energy reserves.

            Able Crew/Maximum Crew - The number of crew who are alive and uninjured, as well as the maximum number of crew that the ship can hold.

            Injured Crew/Maximum Crew - The number of injured crew, as well as the maximum number of crew that the ship can hold.

        ii. Torpedo Information:

            If the player's ship class is capable of firing torpedoes, then the following will be displayed:

            Torpedo Tubes - The maximum number of torpedoes that the player can fire at a time .

            Max Torpedoes - The maximum number of torpedoes that the player's ship can carry.

            Also, the current number of torpedoes for each type that the player can fire.

        ii System Information:

            Each ship system will have a display that shows it's current integrety.

            Most systems, like impulse engines, sensors, and warp drive, are present on all ships, however, some such as torpedoes and beam arrays may 
            be absent.

    G. Selected Ship/Planet/Star Information:

        When the player clicks on a ship, planet, or star on the system sub screen, their selection will change to the object that they click on. If 
        they click on a grid square that is empty, the selection will be cleared.

        Ships will display the same type of information as on the Player Ship Information sub screen.

        Planets will display their system position, status, and current infrastructure development.

        Stars will display their system position and classification.

5. Commands:

    A. Warp:

        This allows the player to travel to different systems. Warp travel is power hungry, and costs much more energy then impulse travel, especially 
        with higher warp speeds. If the warp drive has been damaged, then the energy cost increases.

        There are two ways of entering the destination. If the option "Easy Warping" has been selected, then all the player needs to do is enter the 
        coordinates of the destination system. This can be done manually or by clicking on the sector map.

        The other way consists of entering the heading and destination.

        In each method the expected warp energy cost is displayed.

        After a ships warps into a new system, it will automaticly scan nearbye systems using it's long range scanners

    B. Shields:

        The shields command is used to raise, lower, or modify the shield strength. Here, energy can be transferred to and from the shields.

        The 'Min' and 'Max' buttons will set the shield values to zero and the highest that the ship can support, respectivly.

        The maximum value is affected by damage to the shield system.

    C. Polarize Hull:

        Back in the days before shield generators, ships had to made do by polarizing their hull. The controls are pretty much the same as the shields 
        even if the mechinism is diffrent. 

    D. Move:

        Allows the player to move from one part of the system to another. Travel by impulse engine costs 100 units of energy per distance unit.

        Aside from that, this is mostly the same as the Warp command.

    E. Repair:

        This will let the player commence repairs on their ship. During this, the crew on the player's ship will focusing repairing the hull and any 
        damaged systems, as well as regenerating energy at an increased rate.

        Damage to the warp core will reduce the amount of energy restored.

        For every consecutive turn spent repairing, the amount of of damage that is repaired is increased, as is the amount of energy restored. Taking 
        damage will reset this counter.

    F. Cloaking:

        Some ships have a cloaking devince installed on them. This will allow them to cloak, hiding themselves from detection and making it much more 
        difficult for hostile ships to target them. This does not, however, render the cloaked ship immune from harm, especially since shields are 
        offline while cloaked. Should the cloaked ship sustain damage, say from an errant torpedo or the warp core breach of another ship, then the 
        results will be much worse then if it had been hit while uncloaked.
        
        It is hard to detect a cloaked ship, it is not impossible. If an enemy ship has sensors that are good enough, then the cloaked ship will be 
        (temporarily) revealed to any enemies in the system, and can then be targeted. Note that each enemy ship has a chance to detect the cloaked ship. 
        This is affected by damage to the cloaking device and the sensors of the cloaked, and hostile ships, respectivly.

        After cloaking, a ship may fire torpedos or energy weapons. This will automaticly decloak the ship, so there is no need to manually drop the 
        cloak and give the enemy a free turn to shoot. However, the decloak-fire sequence will overstress the device, and require to wait until a 
        cooldown expires before the ship can cloak again.

    G. Dock:

        If the player is adajacent to a planet that is able and willing to resupply them, then the player is able to dock with the planet. The player may 
        not dock while there are nearbye enemy ships, nor while they are cloaked.

        Docking will allow for increased repairs and energy restoration based on the infrustructure level of the planet.
        
        This may also replenish the player's torpedo reserves, depending if the planet has an infrustructure level equal to or higher to the torpedoes 
        that the player can load.

    H. Fire Beam Arrays:

        This will probably be the primary means of dealing damage to the hostile ships.

        Once an enemy ship has been selected, the user enters the amount of power they want to use, then clicks the button "Fire".

        Alternitvly, they can click the button "Fire All", which distributes the damage evenly amonge all enenmy ships in the system.

        As with the Shields command, the buttons Max and Min are present, with the same functionality.

    I. Fire Cannons:

        Some ships possess cannons in addition to or instead of beam arrays. Cannons are significantly more powerful then beam arrays, but are less 
        accuract, especially at a distance. Cannons can only target a singel enemy ship.
        
        As with beam arrays, the amound of power to use can be ajusted by inputting it directly, or by clicking on the Min and Max buttons.

    J. Fire Torpedoes:

        If the player has checked the option "Easy Aim", then they will only need to enter the coordinates of the target, otherwise they will need to 
        enter the heading. 

        By default, one torpedo will be fired. Should the player's ship have more then one torpedo tube, then they can select the number of torpedoes 
        they want to fire.

    K. Transport:

        The player may choose to beam a number of uninjured crew members over to another starship. The starship must be a derelict, or it must be a 
        friendly craft. If it is a derelict, then the crew members who beamed aboard will take controll of it, allowing it to aperate as a friendly 
        spacecraft. If it is not a derelict, but it is an allied ship, they will renforce the existing crew.  If it is not a derelict and is an enemy 
        ship, the boarding party will fight the crew for control of the ship.

        The player may wish to beam a boarding party off the ship. This can be done by setting the Boarding Team bolean to Retrive, and then deciding 
        how many crew members you want to beam back.

        The player cannot transport crew onto an automated spacecraft. Nor can they transport more crew to a friendly spaceship then the spacecraft's 
        maximum crew.

    L. Auto Destruct:

        In times of desperation, the player may want to self destruct their space craft. Because of the severity of this situation, the player is 
        required to input a password to confirm. The password is displayed below the text entry element.

6. Combat:

    A. Taking Damage:

        Damage can be inflicted on ships thru several ways, however the most common are beam arrays and torpedoes.

        i. Beams:

            Beam arrays have a greater chance of incliting damage on starship systems, and will do a greater amount of damage to systems, however they 
            suffer from a small accuracy penalty.

        ii. Cannons:

            Cannons inflict much more damage per unit of energy then beam weapons, however their accuracy suffers at long range.

        iii. Torpedoes:

            Because of their detonation mechinism, torpedoes do one quarter less damage to shields. Conversly, damage that manadges to 'bleed through' 
            the shields is increased by fifteen percent. And should a torpedo hit a ship with it's shields down, then damge is increased by three 
            quarters. Torpedoes suffer from a small flat accuacy penalty.

        If a ships hull is reduced to less then half its negative hull strength, then it suffers a warp core breach and is totaly destroyed, damaging 
        (and possibly destroying) any ships nearby.

        Normaly, a ship's shield will absorb any damage, however once it is below 50% the ship will begin to experince 'bleed through' damage. The 
        amount to damage that bleeds through increases as the shield percentage decreases, so if a ship's shield is at 25%, then the shield will absorb 
        half of the damage, and the other half will be applied to the hull.

        If the hull is polarized, then damage is reduced by the following formula:

            damage inflicted = max((damage - polarization) + exp(damage / polarization), exp(damage / polarization))

        About 15% of the damage inflicted on a ship will be permanent. What this means is that is that it cannot be fixed by normally and must be 
        repaired by docking with a station or planet.

    B. Systems Damage:

        As a ship's hull is depleted, the change of damaging internal system increases. Starship systems can take quite a bit of beating before they 
        begin to show signs of reduced performance. Generaly, when the systems integrety dips below 80% is when you will see performance degrade. Should 
        integrety fall below 15%, then the system is useless and inoperative until it can be repaired.
        
        Damage to systems will affect ships functionality in different ways:

        i. Impulse:

            Decreases chances of dodging enemy weapons fire, increases energy cost for in-system movment.

        ii. Warp Drive:

            Increases energy cost for warp travel.

        iii. Beam Arrays:

            Decreases the damage and accuracy of beam attacks.

        iv. Cannons:

            Decreases the damage and accuracy of cannon attacks.
        
        v. Torpedoes:

            Decreases the accuracy of torpedoes fired and the number of avaliabe torpedo tubes.

        v. Cloaking Device:

            Increases the chance of detection. 

        vi. Sensors:

            Decreases accuray beam attacks and torpedoes, as well as information on enemy ships displayed.

        vii. Hull Polarization:

            Reduces the effectiveness of the polarization at reduceing damage to the hull

        vii. Shields:

            Decreases maximum shield strength.

        viii. Scanners:

            Decreases the distance at which you can detect hostile ships and stations.

        ix. Transporters:

            Decreases the number of personel who can be transported, as well as decressing the maximum range that they can be transported.

        x. Life Support:

            Decreases the recovery rate of injured crew. If life support fails, then after several turns crew members will star to die due to exposure.

        xi. Warp Core:

            Decreases energy regeneration and the maximum amount of energy that can be stored, and increases the risk of a warp core breach when hit.

7. Bugs: 

    Sometimes, when an enemy ships shield is down, and it's hull is badly depleated, it will not appear on the system map.

    The AI has trouble calculating torpedo trajectories.