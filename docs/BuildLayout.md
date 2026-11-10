# 빌드와 리소스 경계

`build/`에는 모듈과 테스트의 컴파일 결과만 둔다. 모델, 포맷 픽스처, 백엔드 소스 및 라이선스, 설치 스테이징은 `resources/`에 둔다. `resources/dependencies/`에는 명시적으로 준비한 외부 백엔드의 archive, 소스, provenance 및 설치 prefix가 있으며 bootstrap 시 컴파일 중간 결과는 `build/dependency-build/`에 둔다. 일반 `install-native.sh`는 bootstrap을 자동 수행하지 않고, 사용자가 `IIVISUALCODEC_BOOTSTRAP=1`을 지정할 때만 수행한다.

기존 설치본이나 외부 캐시가 예전 `build/dependencies` 경로를 참조할 수 있다. Unix에서 최상위 `build/`를 구성할 때 기존 `resources/dependencies/`가 있으면 이를 가리키는 호환 링크를 만든다. 다른 파일이나 다른 위치를 가리키는 링크는 덮어쓰지 않는다. Windows에서는 자동 링크를 만들지 않으므로 `resources/dependencies/prefix` 또는 외부에서 제공한 백엔드 prefix를 명시한다. 이전 빌드에서 옮긴 백엔드의 설정 캐시는 경로가 달라 `--resume` 검증에 실패할 수 있으며, 이 경우 해당 백엔드를 새로 구성해야 한다.

파일을 생성하는 CTest 계약은 각각 `resources/.t/`의 충돌 없는 작업 공간을 사용하고 성공 또는 실패 후 정리한다. 이 테스트 도구는 iiFileProvider의 Python 어댑터를 사용하며, 경로는 `IIVISUALCODEC_TEST_PROVIDER_PYTHON_DIR`로 변경할 수 있다. 이것은 테스트 도구의 요구사항이며 iiVisualCodec 공개 라이브러리의 의존성은 아니다. 동시 테스트는 서로의 작업 공간을 삭제하지 않는다. 독립 포맷 호환성 스크립트는 필요한 픽스처를 그때 생성하며 외부 ffmpeg·usdcat 등은 명시적으로 실행할 때만 요구한다.

프로세스가 강제 종료되면 정리 코드가 실행되지 않을 수 있으므로 남은 작업 공간은 사용 여부를 확인한 뒤 정리한다.

설치 staging은 `resources/staging/`의 새 하위 디렉터리만 허용하며 기존 디렉터리를 교체하거나 심볼릭 링크로 범위를 탈출하지 않는다. 기본 설치 위치는 `~/.local/SDK/iiVisualCodec`이며 `IISDK_NATIVE_PREFIX`로 변경할 수 있다. 기존 산출물이나 실행 중인 다른 프로젝트를 삭제하지 않도록 먼저 사용 여부를 확인한다. 과거 다중 빌드·로그 경로는 이력이며 현재 테스트 결과가 아니다.
