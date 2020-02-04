import threading
class bpm_data_updater(threading.Thread):
    daemon = True

    def __init__(self, bpm,use_test_data,signal_transfer_line,new_data_to_show_queue,new_data_to_save_queue):
        super().__init__()
        self.bpm = bpm
        self.use_test_data = use_test_data
        self.signal_transfer_line = signal_transfer_line
        self.new_data_to_show_queue = new_data_to_show_queue
        self.new_data_to_save_queue = new_data_to_save_queue

    def run(self):
        while True:
            update_successful = self.bpm.update_data(testing=self.use_test_data)
            self.bpm.perform_fft()
            self.bpm.perform_signal_reconstruction()
            self.bpm.calc_fwhm()
            if update_successful:
                with self.new_data_to_show_queue.mutex:
                    self.new_data_to_show_queue.queue.clear()
                self.new_data_to_show_queue.put({"oscilloscope_signal":self.bpm.v_arr,"reconstructed_signal":self.bpm.reconstructed_signal,"fwhm":self.bpm.fwhm})
                with self.new_data_to_save_queue.mutex:
                    self.new_data_to_save_queue.queue.clear()
                self.new_data_to_save_queue.put({"oscilloscope_signal":self.bpm.v_arr,
                "reconstructed_signal":self.bpm.reconstructed_signal,"fwhm":self.bpm.fwhm})