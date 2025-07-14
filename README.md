# Piattaforma di Aste Online (ASTEROY)

Questo progetto è una piattaforma web per la gestione di aste online, sviluppata come progetto per il corso di Tecnologie Web. Permette agli utenti di registrarsi come venditori o acquirenti, creare aste, fare offerte e lasciare feedback.

## Tecnologie Utilizzate

* **Backend:** Python, Django, Django Channels
* **Database:** SQLite (default di Django)
* **Frontend:** HTML, CSS, JavaScript, Bootstrap
* **Librerie JavaScript:** noUiSlider (per il range slider dei prezzi)
* **Ambiente:** Pipenv per la gestione delle dipendenze

## Prerequisiti

Assicurati di avere installato sul tuo sistema:
* Python (versione 3.10 o superiore)
* Pipenv

## Istruzioni per l'Installazione e l'Avvio

1.  **Clonare il Repository**
    ```bash
    git clone <URL_DEL_TUO_REPOSITORY>
    cd ASTEROY
    ```

2.  **Installare le Dipendenze**
    Usa Pipenv per creare l'ambiente virtuale e installare tutte le librerie necessarie dal `Pipfile.lock`.
    ```bash
    pipenv install
    ```

3.  **Attivare l'Ambiente Virtuale**
    Ogni volta che apri un nuovo terminale per lavorare al progetto, esegui questo comando:
    ```bash
    pipenv shell
    ```

4.  **Creare il Database**
    Esegui le migrazioni per creare le tabelle del database.
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Creare un Superutente**
    Per accedere all'area di amministrazione, crea un superutente.
    ```bash
    python manage.py createsuperuser
    ```

6.  **Avviare il Server**
    Lancia il server di sviluppo. L'applicazione sarà disponibile all'indirizzo `http://127.0.0.1:8000/`.
    ```bash
    python manage.py runserver
    ```

7.  **Eseguire i Test**
    Per lanciare la suite di test automatici, esegui:
    ```bash
    python manage.py test aste
    ```

---

# Online Auction Platform (ASTEROY)

This project is a web platform for managing online auctions, developed as a project for the Web Technologies course. It allows users to register as sellers or buyers, create auctions, place bids, and leave feedback.

## Technologies Used

* **Backend:** Python, Django, Django Channels
* **Database:** SQLite (Django default)
* **Frontend:** HTML, CSS, JavaScript, Bootstrap 4
* **JavaScript Libraries:** noUiSlider (for the price range slider)
* **Environment:** Pipenv for dependency management

## Prerequisites

Ensure you have the following installed on your system:
* Python (version 3.10 or higher)
* Pipenv

## Installation and Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd ASTEROY
    ```

2.  **Install Dependencies**
    Use Pipenv to create the virtual environment and install all required libraries from the `Pipfile`.
    ```bash
    pipenv install
    ```

3.  **Activate the Virtual Environment**
    Each time you open a new terminal to work on the project, run this command:
    ```bash
    pipenv shell
    ```

4.  **Create the Database**
    Run the migrations to create the database tables.
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create a Superuser**
    To access the admin panel, create a superuser.
    ```bash
    python manage.py createsuperuser
    ```

6.  **Start the Server**
    Launch the development server. The application will be available at `http://127.0.0.1:8000/`.
    ```bash
    python manage.py runserver
    ```

7.  **Running Tests**
    To run the automated test suite, execute:
    ```bash
    python manage.py test aste
    ```    