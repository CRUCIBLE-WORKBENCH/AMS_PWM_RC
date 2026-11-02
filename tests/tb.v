`timescale 1ns/1ps
module tb;
reg clk=0,rst=0,psel=0,penable=0,pwrite=0;
reg [7:0] addr=0;
reg [31:0] wdata=0;
wire ready,err,pwm;
wire [31:0] rdata;
integer checks=0,target,c,frame,highs,fd;
reg [1023:0] path;
always #500 clk=~clk;
apb_pwm dut(clk,rst,psel,penable,pwrite,addr,wdata,ready,err,rdata,pwm);
task check;
input condition;
input [255:0] label;
begin checks=checks+1; if(condition !== 1'b1) $fatal(1,"APB_PWM_MISMATCH %0s",label); end
endtask
task transfer;
input wr;
input [7:0] a;
input [31:0] d;
input bad;
begin
    @(negedge clk);psel=1;penable=0;pwrite=wr;addr=a;wdata=d;
    @(negedge clk);penable=1;#1;check(ready,"ready");check(err===bad,"error response");
    @(negedge clk);psel=0;penable=0;pwrite=0;
end
endtask
task readback;
input [7:0] a;
input [31:0] expected;
begin
    transfer(0,a,0,0);#1;check(rdata===expected,"readback");
end
endtask
initial begin
    repeat(3)@(negedge clk);rst=1;
    readback(0,0);readback(4,0);check(pwm===0,"reset output");
    // A setup phase held across edges must not perform a write.
    @(negedge clk);psel=1;penable=0;pwrite=1;addr=4;wdata=128;
    repeat(3)@(negedge clk);check(rdata===0,"setup has no side effects");
    psel=0;pwrite=0;
    transfer(1,4,64,0);readback(4,64);
    transfer(1,4,257,1);readback(4,64);
    transfer(1,8,99,1);readback(4,64);
    transfer(1,1,99,1);readback(0,0);
    for(target=0;target<=256;target=target+64) begin
        transfer(1,0,0,0);check(pwm===0,"disable output");
        transfer(1,4,target,0);readback(4,target);
        transfer(1,0,1,0);readback(0,1);
        $sformat(path,"results/digital_%0d.csv",target);fd=$fopen(path,"w");
        if(!fd)$fatal(1,"TRACE_OPEN_FAILED");
        $fdisplay(fd,"time_ns,logic");
        for(frame=0;frame<80;frame=frame+1) begin
            highs=0;
            for(c=0;c<256;c=c+1) begin
                @(negedge clk);check(pwm===0 || pwm===1,"known PWM");
                if(pwm)highs=highs+1;
                $fdisplay(fd,"%0d,%0d",(frame*256+c)*1000,pwm);
            end
            check(highs==target,"period high count");
        end
        $fclose(fd);
        $display("PWM_CASE duty=%0d periods=80",target);
    end
    transfer(1,0,0,0);check(pwm===0,"final disable");
    rst=0;#1;addr=4;check(rdata===0,"reset clears duty");check(pwm===0,"reset low");
    $display("APB_PWM_DIGITAL_PASS checks=%0d",checks);$finish;
end
initial begin #120000000;$fatal(1,"TEST_TIMEOUT");end
endmodule
