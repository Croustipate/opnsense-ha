# OPNsense Firmware Update — intégration Home Assistant

Intégration non-officielle pour Home Assistant permettant de :
- savoir si le firewall OPNsense a une mise à jour firmware/paquets disponible (`sensor.opnsense_firmware`)
- déclencher une vérification immédiate (`button.opnsense_check_now`)
- déclencher la mise à jour (`button.opnsense_install_update`)
- suivre le résultat de la dernière mise à jour déclenchée (`sensor.opnsense_last_update`)

## Installation

1. Copier le dossier `custom_components/opnsense` dans `config/custom_components/opnsense` de ton instance Home Assistant.
2. Redémarrer Home Assistant.
3. Paramètres > Appareils et services > Ajouter une intégration > rechercher "OPNsense".
4. Renseigner l'URL du firewall, la clé API et le secret API (générés dans OPNsense : Système > Accès > Utilisateurs > onglet clés API).

## Notes

- Le bouton "Installer la mise à jour" est désactivé tant qu'aucune mise à jour n'est détectée.
- Le firewall redémarre automatiquement si la mise à jour l'exige ; le suivi (`sensor.opnsense_last_update`) tolère une perte de connexion jusqu'à 15 minutes pendant ce redémarrage.
