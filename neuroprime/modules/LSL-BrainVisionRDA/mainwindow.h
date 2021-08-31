#pragma once

#include <QtWidgets/QMainWindow>
#include "ui_mainwindow.h"

#include <QCloseEvent>
#include <QFileDialog>
#include <QMessageBox>
#include <boost/shared_ptr.hpp>
//#include <boost/thread.hpp>
#include <thread>
#include <string>
#include <vector>

// LSL API
#include <lsl_cpp.h>

#define WIN32_LEAN_AND_MEAN
#include "windows.h"

namespace Ui {
    class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:

    explicit MainWindow(QWidget* parent, const std::string& config_file);
    ~MainWindow();
    struct t_AppVersion {
        int32_t Major;
        int32_t Minor;
    };
    t_AppVersion m_AppVersion;

private slots:
    // config file dialog ops (from main menu)
    void load_config_dialog();
    void save_config_dialog();
    void set_port(int idx);
    // start the BrainVision RDA connection
    void link_rda();
    void versions_dialog();
    // close event (potentially disabled)
    void closeEvent(QCloseEvent* ev);

    // status messages
    void statusMessage(QString msg);

signals:
    void sendMessage(QString msg);

private:
    // raw config file IO
    void load_config(const std::string& filename);
    void save_config(const std::string& filename);

    // background data reader thread
    void read_thread(QString serverIP);
    int RDA_Port;
    bool stop_;											// whether the reader thread is supposed to stop
    std::unique_ptr<std::thread> reader_thread_;
    //boost::shared_ptr<boost::thread> reader_thread_;	// our reader thread
    Ui::MainWindow* ui;
};


