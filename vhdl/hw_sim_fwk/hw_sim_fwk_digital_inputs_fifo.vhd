
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;
use hw_sim_fwk.hw_sim_fwk_common.all;

-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_digital_inputs_fifo is
    generic(
        NR_DIS             : integer := 2;
        FIFO_PATH          : string  := "\\.\pipe\";
        DIS_FILE_NAME      : string  := FIFO_PATH & "di_";
        PROTOCOL_DIS       : boolean := false
    );
    port(
        reset     : in  std_logic;
        clock     : in  std_logic;
        hw_di     : out std_logic_vector(NR_DIS - 1 downto 0)
    );
end hw_sim_fwk_digital_inputs_fifo;

architecture arch of hw_sim_fwk_digital_inputs_fifo is
begin
    -- instantiate hw digital inputs simulated externally
    -- ##################################################
    -- NOTE: it is not possible to create an array of files or objects with files to be used in only one instance of the logic.
    --       Therefore, the process is instantiated NR_DIS times.
    --       Note that DOs are implemented by generating NR_DOS instances of hw_sim_fwk_digital_output instead.
    GEN_DIS:
    for i in 0 to (NR_DIS - 1) generate
        -- DI_x reading process
        -- ####################
        proc_update_dis_x : process(reset, clock)
        -- proc_update_dis_x : process(reset, clock)
            variable initialized : boolean := false;
            variable resetted : boolean := false;
            variable open_status : FILE_OPEN_STATUS;
            -- NOTE: it is not possible to create an array of files or
            --       including file type inside of a Record structure
            file i_file : text;
            variable i_line : line;
            -- NOTE: the variable "stimulus" could mean di_level or edge_transition, but it does not matter
            --       because to keep things consistent we check in addition against the variable "pos_level".
            variable stimulus   : std_logic;
            variable pos_level : boolean := false;   
        begin
            -- initialization
            -- ##############
            if initialized = false then
                initialized := true;                
                if (PROTOCOL_DIS = true) then
                    report "simulated HW DI "&integer'image(i)&" waiting to open for read on FIFO.";
                end if;
                -- The file, which is a FIFO (named pipe), is created by the external application.    
                loop
                    file_open(open_status, i_file, DIS_FILE_NAME & integer'image(i),  read_mode);
                    exit when open_status = open_ok;
                end loop;                  
                if (PROTOCOL_DIS = true) then
                    report "simulated HW DI "&integer'image(i)&" opened for read on FIFO.";
                end if;
            -- asynchronous reset
            -- ##################
            elsif reset = '1' then 
                -- initialize DI only once during reset
                if resetted = false then
                    resetted := true;
                    -- "block" until new line is sent (no CPU consumption!)
                    -- WARNING!
                    --         in VIVADO the complete simulation blocks. Processes are not concurrent in this particular case.
                    --         If DIs are all set once within each clock period, then this implementation can be used.
                    ----------------------------------------------------------------------------------------------------------
                    readline(i_file, i_line);
                    read(i_line, stimulus);            
                    -- initialize digital input signal
                    if (stimulus = '1') then
                        hw_di(i) <= '1';
                        pos_level := true;
                        if (PROTOCOL_DIS = true) then
                            report "hw_di_"&integer'image(i)&" initialized to 1";
                        end if;
                    -- all other values are initialized to zero
                    else
                        hw_di(i) <= '0';
                        pos_level := false;
                        if (PROTOCOL_DIS = true) then
                            report "hw_di_"&integer'image(i)&" initialized to 0";
                        end if;
                    end if;                                        
                end if; -- if resetted = false
            -- synchronous events    
            elsif rising_edge(clock) then
            -- TODO: check this..
            -- elsif rising_edge(clock) or falling_edge(clock) then -- detect DI changes in both clock edges to give async DIs a chance to be seen (?)            
            -- else -- similar behavior as: elsif rising_edge(clock) or falling_edge(clock) then
                if (PROTOCOL_DIS = true) then
                    report "checking dis_rising/falling_edge on DI = " & integer'image(i);
                end if;                    
                -- "block" until new line is sent (no CPU consumption!)
                -------------------------------------------------------
                readline(i_file, i_line);
                read(i_line, stimulus);     
                -- rising edge?
                if pos_level = false then
                    if (stimulus = '1') then
                        if PROTOCOL_DIS = true then
                            report "digital input rising ege on DI = " & integer'image(i);
                        end if;
                        pos_level := true;
                        hw_di(i) <= '1';
                    end if;
                -- falling edge?
                elsif (stimulus = '0') then
                    if PROTOCOL_DIS = true then
                        report "ditial input falling ege on DI = " & integer'image(i);
                    end if;
                    pos_level := false;
                    hw_di(i) <= '0';
                end if;
            end if; -- if initialized
        end process proc_update_dis_x;
    end generate GEN_DIS;
end architecture arch;

-- synthesis translate_on
-- ######################





