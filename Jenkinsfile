pipeline {
    agent none 
    stages {

        environment { 
                PYLINT_REPORT_DIR = '$(pwd)/py-lint-reports'
                PYLINT_REPORT_FILE_NAME = 'index.html'
                PYLINT_REPORT_NAME = 'Pylint Report'
            }

        /*
        stage('Build') { 
            agent {
                docker {
                    image 'python:3.11.4-alpine3.18' 
                }
            }
            steps {
                sh 'python -m py_compile sources/add2vals.py sources/calc.py' 
                stash(name: 'compiled-results', includes: 'sources/*.py*') 
            }
        }
        */
        stage('CodeCheck') { 
            agent {
                docker {
                    image 'cytopia/pylint:latest' 
                }
            }
            steps {
                sh 'pylint argcat.py --output ${PYLINT_REPORT_FILE_NAME}' 
                //stash(name: 'pylint-result', includes: 'pylint-report.html')

                dir(path: "${PYLINT_REPORT_DIR}") { 
                    sh "mv ${PYLINT_REPORT_FILE_NAME} ${PYLINT_REPORT_DIR}" 
                }

                publishHTML(
                    [allowMissing: false, 
                    alwaysLinkToLastBuild: false, 
                    keepAll: false, 
                    reportDir: ${PYLINT_REPORT_DIR}, 
                    reportFiles: ${PYLINT_REPORT_FILE_NAME}, 
                    reportName: ${PYLINT_REPORT_NAME}, 
                    reportTitles: ${PYLINT_REPORT_NAME}, 
                    useWrapperFileDirectly: true]
                    )      

            }
        }

        /*
        stage('Test') { 
            agent {
                docker {
                    image 'qnib/pytest' 
                }
            }
            steps {
                sh 'py.test --junit-xml test-reports/results.xml sources/test_calc.py' 
            }
            post {
                always {
                    junit 'test-reports/results.xml' 
                }
            }
        }
        */
        /*
        stage('Deliver') { 
            agent any
            environment { 
                VOLUME = '$(pwd)/sources:/src'
                IMAGE = 'cdrx/pyinstaller-linux:python2'
            }
            steps {
                dir(path: env.BUILD_ID) { 
                    unstash(name: 'pyline-result') 
                    sh "docker run --rm -v ${VOLUME} ${IMAGE} 'pyinstaller -F add2vals.py'" 
                }

                          
            }
            post {
                success {
                    archiveArtifacts "${env.BUILD_ID}/sources/dist/add2vals" 
                    sh "docker run --rm -v ${VOLUME} ${IMAGE} 'rm -rf build dist'"
                }
            }
        }
        */
    }
}