if(NOT TARGET_TYPE STREQUAL "SHARED_LIBRARY")
    message(FATAL_ERROR "A shared codec component was requested but target type is ${TARGET_TYPE}")
endif()
