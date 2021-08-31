cmake_minimum_required(VERSION 3.5)
project(BrainVisionRDA
	LANGUAGES CXX
	VERSION 0.1.0)

# load LSLAppBoilerplate if not done already
if(NOT TARGET LSL::lsl)
	if(NOT LSL_INSTALL_ROOT)
		message(FATAL_ERROR "When building a single app out of tree you need to set LSL_INSTALL_ROOT ( cmake -DLSL_INSTALL_ROOT=/path/to/installed/lsl)")
	endif()
	if(NOT IS_ABSOLUTE ${LSL_INSTALL_ROOT})
		message(FATAL_ERROR "LSL_INSTALL_ROOT needs to be an absolute path")
	endif()
	file(TO_CMAKE_PATH ${LSL_INSTALL_ROOT} LSL_INSTALL_ROOT)
	list(APPEND CMAKE_MODULE_PATH "${LSL_INSTALL_ROOT}/cmake")
	include(LSLAppBoilerplate)
endif()


# GENERAL CONFIG #
cmake_policy(SET CMP0028 NEW) # ENABLE CMP0028: Double colon in target name means ALIAS or IMPORTED target.
cmake_policy(SET CMP0054 NEW) # ENABLE CMP0054: Only interpret if() arguments as variables or keywords when unquoted.
cmake_policy(SET CMP0063 NEW) # ENABLE CMP0063: Honor visibility properties for all target types.

# META CONFIG #
set(META_PROJECT_DESCRIPTION "Stream from BrainVision Recorder's RDA client via Lab Streaming Layer")

# THIRD PARTY LIBRARIES #
find_package(Qt5 COMPONENTS Xml Widgets REQUIRED)
find_package(Boost REQUIRED COMPONENTS thread)

# Target name
set(target BrainVisionRDA)

# Sources
set(sources
	main.cpp
	mainwindow.cpp
	mainwindow.h
	mainwindow.ui
	rda_client.h
	rda_message.h
	regression.h
)

# Add executable target
add_executable(${target} MACOSX_BUNDLE WIN32 ${sources})

target_link_libraries(${target}
	PRIVATE
	Qt5::Widgets
	Qt5::Xml
    Qt5::Gui
    Qt5::Core
	Boost::thread
	LSL::lsl
)

# Boost includes needed here because they aren't pulled in by any linked library above
target_include_directories(${target} PRIVATE ${Boost_INCLUDE_DIRS})

# Deployment
installLSLApp(${target})
install(FILES default_config.cfg
	DESTINATION ${PROJECT_NAME})
	
installLSLAuxFiles(${target} Qt5Core.dll Qt5Gui.dll Qt5Widgets.dll)
