<?php

updateHE();

function updateHE() {
    echo "Actualizando...\n";
    $update = "/home/ubuntu/update.zip";

    // Por si acaso ya existe la carpeta update, se elimina
    if (file_exists("/home/ubuntu/update")) {
        exec("rm -R /home/ubuntu/update");
    }
    // Si existe el update.zip, lo descomprimimos y empezamos la actualización
    if (file_exists($update)) {
        if (exec("unzip -P uvax1008 " . $update . " -d /home/ubuntu/")) {

            exec("/home/ubuntu/update/update.sh > /home/ubuntu/update_log.txt");

            exec("touch /home/ubuntu/update.flag");

            // Limpiamos la carpeta update y el zip
            exec("rm -R /home/ubuntu/update/");
            exec("rm " . $update);
            exec("rm /home/ubuntu/updateHE.php");
        }
    } else {
        exec("rm /home/ubuntu/update.flag");
    }
}
