pipeline {
    agent none 
    stages {
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
                mkdir 'py-lint-reports'
                sh 'pylint argcat.py --output py-lint-reports/index.html' 
                //stash(name: 'pylint-result', includes: 'pylint-report.html')

                publishHTML(
                    [allowMissing: false, 
                    alwaysLinkToLastBuild: false, 
                    keepAll: false, 
                    reportDir: 'py-lint-reports', 
                    reportFiles: 'index.html', 
                    reportName: 'Pylint Report', 
                    reportTitles: 'Pylint Report', 
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