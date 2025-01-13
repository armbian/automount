cmake_minimum_required(VERSION 3.16) # focal
project(automount VERSION 0.1)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

include(GNUInstallDirs)

install(FILES main.py monitor.py util.py
    DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/automount/
)

configure_file(automount.service.in automount.service @ONLY)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/automount.service
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/systemd/system/
)

install(FILES 30-default.conf
    DESTINATION ${CMAKE_INSTALL_DATADIR}/automount/
)
