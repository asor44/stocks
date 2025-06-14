{pkgs}: {
  deps = [
    pkgs.libmysqlclient
    pkgs.mysql-client
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.postgresql
    pkgs.openssl
  ];
}
