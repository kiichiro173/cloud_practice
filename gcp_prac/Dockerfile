# データサイエンス仮想環境　
# anacondaの環境を作成している。
# anacondaのサイトは以下
# https://repo.anaconda.com/archive/
# ubuntuの場合はLinux-x86
# このdockerfileを使用してデータ分析等を行う場合は以下の手順
# docker build .
# docker images イメージができているか確認
# docker run -p ローカルのポート:8888 -v マウントしたいディレクトリ:dockerのマウント先 --name my-lab イメージID
# docker run -p 1234:8888 -v /Users/kiichiro/Desktop/data/scikit_learn_practice/src:/work --name my-lab 0ffa1ee223d4
# あくまでもファイルはホスト側にある（dockerfileにはないので注意が必要。）

FROM ubuntu:latest
RUN apt-get update && apt-get install -y \
    sudo \
    wget \
    vim
WORKDIR /opt
# もしバージョンを変えたい場合は以下のサイトの部分を変更する。
RUN wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh && \
    bash Anaconda3-2021.11-Linux-x86_64.sh -b -p /opt/anaconda3 && \
    rm -f Anaconda3-2021.11-Linux-x86_64.sh

# パスを通す
ENV PATH=/opt/anaconda3/bin:$PATH
RUN pip install --upgrade pip
WORKDIR /
# デフォルトのコマンドの指定
CMD [ "jupyter","lab", "--ip=0.0.0.0" , "--allow-root", "--LabApp.token=''"]

EXPOSE 8888