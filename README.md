# theodorblom.com

![Run Pytest](https://github.com/Theeoi/theodorblom.com/actions/workflows/test.yml/badge.svg?label=Tests)

The personal website of Theodor Blom.
The website is run as a Flask instance on a VPS.

## General Information

I believe everyone should have a personal website and decided it would be more
fun to build it from scratch than use one of the many hosting services. The
goal of the website is to act as a mix of CV, portfolio and a creative hub.

### Technologies

- Python 3.8<=
- Flask 2.2<=
- Pytest 7.3<=

### Features

- A welcome page with links to my socials.
- A sticky mobile-friendly navbar.
- An animated favicon.
- A blogging module with Markdown-support.
- A user authentication system for admin access.
- Basic logging of website activity including hit statistics.
- A full testing suite with Pytest.
- More features coming. See [Project Status](#project-status)

## Setup

Setup is not required unless you want to explore the dev branch and/or
[contribute](#contributing).

### Usage

1. Go to [www.theodorblom.com](https://www.theodorblom.com) and enjoy!

### Contributing

If you found an error or have suggestions for further development, please
submit an issue! <3

To contribute you have to set up your own instance of the app. Settings for
your instance are made in the 'config.py' file in the 'instance' directory.
Default development settings are found in 'config.py'.

1. Clone the repo `git clone https://github.com/Theeoi/theodorblom.com`
2. Go into the directory `cd theodorblom.com`
3. Install requirements `pip install -r requirements.txt`
4. Run the app `python app.py`
5. View the webpage at [127.0.0.1:5000](http://127.0.0.1:5000)

Please note:
To create an account to store in the database, remove the `@login_required` on
the create_user route. Remember to revert the changes after storing the user in
the database.

## Project Status

The website is up but is being developed sporadically.

### Roadmap

Todo:

- [x] Create a login system for admin access
- [x] Build a blog
- [x] Implement a statistics page
- [ ] Add request filtering to the stats page
- [ ] Add blogpost filtering based on tags
- [ ] Implement a FTP for file transfers (Useful for hosting blog images).

Room for improvement:

- Improve logging
- Improve the stats page

## Contact

Created by [@theodorblom](https://www.theodorblom.com) - feel free to contact
me!
