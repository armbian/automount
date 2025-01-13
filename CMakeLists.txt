cmake_minimum_required(VERSION 3.16) # focal
project(automount VERSION 0.1 LANGUAGES C)

include(GNUInstallDirs)

configure_file(util.py util.py @ONLY)
install(FILES main.py monitor.py ${CMAKE_CURRENT_BINARY_DIR}/util.py
    DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/automount/
)

configure_file(automount.service automount.service @ONLY)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/automount.service
    DESTINATION lib/systemd/system/
)

install(FILES 10-default.conf
    DESTINATION ${CMAKE_INSTALL_DATADIR}/automount/
)
