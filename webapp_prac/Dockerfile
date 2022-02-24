# RailsのDockerfile作成
# docker run -it -v /Users/kiichiro/Desktop/data/docker_practice/webapp_prac:/product-register -p 3000:3000 519611b168e2 bash
FROM ruby:2.5
RUN apt-get update && apt-get install -y \
    build-essential\
    libpq-dev\
    nodejs \
    postgresql-client\
    yarn

WORKDIR /product-register
COPY Gemfile Gemfile.lock /product-register/
RUN bundle install