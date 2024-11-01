To run in pycahrm:
1. Create new environment
python3 -m venv .venv/
2. Activate it
source .venv/bin/activate
3. Install all needed pip packages
pip3 install -r requirements.txt
4. Generate requirements.txt after release and use it while container build
pip3 freeze > requirements.txt
5. Set env variables to run te app (see docker compose)
6. Git
Create new repo in github
create  local .gitignore
After:
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:dmzopi/myBlog.git
git push -u origin main
…or push an existing repository from the command line
git remote add origin git@github.com:dmzopi/myBlog.git
git branch -M main
git push -u origin main







To run in production:
1. get the git code
2. docker build -t blog_app:1 .
3. docker compose up -d





